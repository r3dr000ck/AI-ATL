#!/usr/bin/env python3
"""
ai_trader_news2signal.py

One-file pipeline:
  - Scrape reputable sources (Reuters/AP/Yahoo/CNBC/MarketWatch) via RSS
  - Extract full text; build embeddings (OpenAI 'text-embedding-3-small' or SentenceTransformers MiniLM)
  - Save CSV with columns: title,date,url,country,language,source,emb_0..emb_N
  - Merge embeddings with 5-min META bars, train LightGBM/XGBoost/LogReg
  - Output metrics + cumulative return plot

USAGE EXAMPLES
--------------
# 1) Create embeddings with OpenAI (set your API key first):
export OPENAI_API_KEY=sk-...
python ai_trader_news2signal.py embed --out meta_emb.csv --since 2024-01-01 --until 2024-03-01 --tickers META --use_openai

# 2) Or create embeddings locally (offline) with SentenceTransformers:
python ai_trader_news2signal.py embed --out meta_emb.csv --since 2024-01-01 --until 2024-03-01 --tickers META

# 3) Train the signal model on META price bars + embeddings CSV:
python ai_trader_news2signal.py train --price_csv colin_stock.csv --emb_csv meta_emb.csv --ticker META --start 2024-01-15 --end 2024-02-15 --p_up 0.60

DEPENDENCIES
------------
pip install pandas numpy requests feedparser beautifulsoup4 readability-lxml langdetect sentence-transformers lightgbm scikit-learn matplotlib
# (optional) pip install openai xgboost
"""

import os, re, sys, argparse
import pandas as pd, numpy as np
import requests, feedparser
from dataclasses import dataclass
from typing import List, Dict, Optional
from bs4 import BeautifulSoup
from readability import Document
from langdetect import detect as lang_detect
import matplotlib.pyplot as plt

# Lazy imports
_SENTENCE_TRANSFORMERS = None
_OPENAI = None
_LGBM = None
_XGB = None

def _lazy_import_sentence_transformers():
    global _SENTENCE_TRANSFORMERS
    if _SENTENCE_TRANSFORMERS is None:
        from sentence_transformers import SentenceTransformer
        _SENTENCE_TRANSFORMERS = SentenceTransformer
    return _SENTENCE_TRANSFORMERS

def _lazy_import_openai():
    global _OPENAI
    if _OPENAI is None:
        from openai import OpenAI
        _OPENAI = OpenAI
    return _OPENAI

def _lazy_import_lightgbm():
    global _LGBM
    if _LGBM is None:
        import lightgbm as lgb
        _LGBM = lgb
    return _LGBM

def _lazy_import_xgboost():
    global _XGB
    if _XGB is None:
        try:
            import xgboost as xgb
            _XGB = xgb
        except Exception:
            _XGB = None
    return _XGB

# -------------------- RSS Sources --------------------

DEFAULT_SOURCES = [
    {"name":"Reuters Business","type":"rss","url":"https://feeds.reuters.com/reuters/businessNews","country":"US"},
    {"name":"AP Top","type":"rss","url":"https://apnews.com/hub/ap-top-news?utm_source=apnews.com&utm_medium=referral&utm_campaign=rss","country":"US"},
    {"name":"Yahoo Finance Top","type":"rss","url":"https://finance.yahoo.com/news/rssindex","country":"US"},
    {"name":"CNBC Markets","type":"rss","url":"https://www.cnbc.com/id/100003114/device/rss/rss.html","country":"US"},
    {"name":"MarketWatch","type":"rss","url":"https://www.marketwatch.com/feeds/topstories","country":"US"},
]

DEFAULT_TICKERS = ["META","NVDA","AAPL","AMZN","MSFT","SPY","QQQ"]
DEFAULT_KEYWORDS = ["Meta","Facebook","Zuckerberg","AI","earnings","FOMC","CPI","guidance","regulation"]

@dataclass
class Source:
    name: str
    type: str
    url: str
    country: Optional[str] = None

def fetch_rss_entries(src: Source):
    d = feedparser.parse(src.url)
    entries = []
    for e in d.entries:
        title = (e.get("title") or "").strip()
        link = (e.get("link") or "").strip()
        published = e.get("published") or e.get("updated") or e.get("pubDate") or ""
        pub_dt = pd.to_datetime(published, utc=True, errors="coerce")
        entries.append({"source": src.name, "country": src.country or "", "title": title, "url": link, "date": pub_dt})
    return entries

def clean_text(text: str) -> str:
    return re.sub(r"\s+"," ", (text or "")).strip()

def fetch_article_html(url: str, timeout: int = 12) -> Optional[str]:
    headers = {"User-Agent": "Mozilla/5.0 (compatible; News2Signal/1.0)"}
    try:
        r = requests.get(url, headers=headers, timeout=timeout)
        if r.status_code == 200 and r.text:
            return r.text
    except Exception:
        return None
    return None

def extract_main_text(html: str) -> str:
    # readability first
    try:
        doc = Document(html)
        content_html = doc.summary()
        soup = BeautifulSoup(content_html, "html.parser")
        txt = clean_text(soup.get_text(separator=" "))
        if len(txt) > 200:
            return txt
    except Exception:
        pass
    # fallback
    try:
        soup = BeautifulSoup(html, "html.parser")
        for tag in soup(["script","style","noscript","header","footer","nav","aside"]):
            tag.decompose()
        return clean_text(soup.get_text(separator=" "))
    except Exception:
        return ""

def filter_by_keywords(entry: Dict, tickers: List[str], keywords: List[str]) -> bool:
    title = (entry.get("title") or "").lower()
    url = (entry.get("url") or "").lower()
    keep_title = any(k.lower() in title for k in keywords) if keywords else True
    keep_ticker = any(t.lower() in title or f"/{t.lower()}" in url for t in tickers) if tickers else True
    return keep_title and keep_ticker

def build_embeddings(texts: List[str], use_openai: bool=False, openai_model: str="text-embedding-3-small", st_model_name: str="sentence-transformers/all-MiniLM-L6-v2") -> np.ndarray:
    if use_openai:
        OpenAI = _lazy_import_openai()
        client = OpenAI()
        out = []
        for t in texts:
            t = t[:7000]  # safety
            resp = client.embeddings.create(model=openai_model, input=t)
            out.append(resp.data[0].embedding)
        return np.array(out, dtype=float)
    else:
        SentenceTransformer = _lazy_import_sentence_transformers()
        model = SentenceTransformer(st_model_name)
        return model.encode(texts, normalize_embeddings=False)

# -------------------- EMBED Subcommand --------------------

def cmd_embed(args):
    # Build Source list
    sources = [Source(**s) for s in DEFAULT_SOURCES]
    # Collect entries
    entries = []
    for src in sources:
        if src.type != "rss": 
            continue
        try:
            entries.extend(fetch_rss_entries(src))
        except Exception as e:
            print(f"[warn] feed failed {src.name}: {e}")
    df = pd.DataFrame(entries)
    if df.empty:
        print("No entries found."); return

    # Date filter
    df["date"] = pd.to_datetime(df["date"], utc=True, errors="coerce")
    df = df.dropna(subset=["date"]).sort_values("date")
    if args.since:
        df = df[df["date"] >= pd.Timestamp(args.since, tz="UTC")]
    if args.until:
        df = df[df["date"] <= pd.Timestamp(args.until, tz="UTC")]

    # Keyword/Ticker filters
    tickers = args.tickers or DEFAULT_TICKERS
    keywords = args.keywords or DEFAULT_KEYWORDS
    if tickers or keywords:
        mask = df.apply(lambda r: filter_by_keywords(r, tickers, keywords), axis=1)
        df = df[mask]

    df = df.drop_duplicates(subset=["url"], keep="last")
    if df.empty:
        print("No entries after filters."); return

    rows, texts = [], []
    for _, r in df.iterrows():
        if args.max_articles and len(rows) >= args.max_articles:
            break
        html = fetch_article_html(r["url"])
        if not html:
            continue
        text = extract_main_text(html)
        if len(text) < 200:
            continue
        try:
            lang = lang_detect(text)
        except Exception:
            lang = "unknown"
        rows.append({
            "title": r["title"],
            "date": r["date"].isoformat(),
            "url": r["url"],
            "country": r.get("country",""),
            "language": lang,
            "source": r.get("source",""),
            "text": text[:12000]
        })
        texts.append(text)

    if not rows:
        print("No parsed articles."); return

    embs = build_embeddings(texts, use_openai=args.use_openai, openai_model=args.openai_model, st_model_name=args.st_model)
    dim = embs.shape[1]
    out_df = pd.DataFrame(rows)
    for j in range(dim):
        out_df[f"emb_{j}"] = embs[:, j]

    cols = ["title","date","url","country","language","source"] + [f"emb_{j}" for j in range(dim)]
    out_df = out_df[cols]
    out_df.to_csv(args.out, index=False, encoding="utf-8")
    print(f"Wrote {len(out_df)} rows with {dim}-dim embeddings to {args.out}")

# -------------------- TRAIN Subcommand --------------------

from sklearn.decomposition import PCA
from sklearn.metrics import accuracy_score, f1_score, roc_auc_score

def load_embeddings_csv(path):
    emb = pd.read_csv(path)
    emb["date"] = pd.to_datetime(emb["date"], utc=True, errors="coerce")
    emb["ts5"] = emb["date"].dt.floor("5min")
    emb_cols = [c for c in emb.columns if c.startswith("emb_")]
    emb_agg = emb.groupby("ts5")[emb_cols].mean().reset_index()
    return emb_agg, emb_cols

def prepare_price_df(price_csv, ticker, start=None, end=None):
    df = pd.read_csv(price_csv)
    df["timestamp"] = pd.to_datetime(df["timestamp"], utc=True)
    df = df[df["ticker"]==ticker].copy()
    if start: df = df[df["timestamp"]>=pd.Timestamp(start, tz="UTC")]
    if end:   df = df[df["timestamp"]<=pd.Timestamp(end, tz="UTC")]
    df["ts5"] = df["timestamp"].dt.floor("5min")
    return df

def train_model(X_train, y_train):
    # Prefer LightGBM, fallback to XGBoost, then LogisticRegression
    lgb = None
    try:
        lgb = _lazy_import_lightgbm()
        model = lgb.LGBMClassifier(
            objective="binary",
            metric="auc",
            learning_rate=0.03,
            num_leaves=63,
            feature_fraction=0.8,
            bagging_fraction=0.9,
            bagging_freq=5,
            reg_lambda=2.0,
            n_estimators=800,
            random_state=42
        )
        model.fit(X_train, y_train)
        return model, "LightGBM"
    except Exception as e:
        pass
    xgb = _lazy_import_xgboost()
    if xgb is not None:
        from xgboost import XGBClassifier
        model = XGBClassifier(
            n_estimators=300,
            max_depth=6,
            learning_rate=0.05,
            subsample=0.9,
            colsample_bytree=0.8,
            reg_lambda=2.0,
            random_state=42,
            n_jobs=-1,
            objective="binary:logistic"
        )
        model.fit(X_train, y_train)
        return model, "XGBoost"
    # Fallback LogisticRegression
    from sklearn.linear_model import LogisticRegression
    model = LogisticRegression(max_iter=300, solver="lbfgs")
    model.fit(X_train, y_train)
    return model, "LogisticRegression"

def cmd_train(args):
    emb_agg, emb_cols = load_embeddings_csv(args.emb_csv)
    price_df = prepare_price_df(args.price_csv, args.ticker, args.start, args.end)
    merged = price_df.merge(emb_agg, on="ts5", how="left")

    # Fill missing embeddings with zeros (no news that window)
    for c in [col for col in merged.columns if col.startswith("emb_")]:
        merged[c] = merged[c].fillna(0.0)

    # Label
    merged["future_close"] = merged["close"].shift(-1)
    merged["target"] = (merged["future_close"] > merged["close"]).astype(int)
    merged = merged.dropna(subset=["target"]).copy()

    # Base features
    base_feats = ["return_5m","price_vs_vwap","rsi_7","QQQ_ret_5m","SPY_ret_5m"]
    base_feats = [c for c in base_feats if c in merged.columns]

    # PCA on embeddings
    emb_cols = [c for c in merged.columns if c.startswith("emb_")]
    if emb_cols:
        emb_mat = merged[emb_cols].to_numpy(dtype=float)
        n_comp = min(max(8, int(0.06*emb_mat.shape[1])), 32)  # 8..32 depending on dim
        pca = PCA(n_components=n_comp, random_state=42)
        emb_pca = pca.fit_transform(emb_mat)
        pca_cols = [f"emb_pca{i}" for i in range(emb_pca.shape[1])]
        X = pd.concat([merged[base_feats].reset_index(drop=True),
                       pd.DataFrame(emb_pca, columns=pca_cols)], axis=1)
    else:
        X = merged[base_feats].copy()

    y = merged["target"].astype(int).values

    # Chrono split
    split = int(0.8*len(X))
    X_train, X_test = X.iloc[:split].fillna(0), X.iloc[split:].fillna(0)
    y_train, y_test = y[:split], y[split:]

    model, model_name = train_model(X_train, y_train)

    # Predict
    proba = None
    try:
        proba = model.predict_proba(X_test)[:,1]
    except Exception:
        # Some linear models may require this
        from sklearn.preprocessing import minmax_scale
        scores = model.decision_function(X_test)
        proba = minmax_scale(scores)

    pred = (proba >= args.p_up).astype(int)

    acc = accuracy_score(y_test, pred)
    f1  = f1_score(y_test, pred, zero_division=0)
    auc = roc_auc_score(y_test, proba)

    print(f"Model={model_name}  Accuracy={acc:.3f}  F1={f1:.3f}  AUC={auc:.3f}  (p_up={args.p_up})")

    # Backtest
    test_slice = merged.iloc[split:].copy()
    test_slice["ret"] = test_slice["close"].pct_change().fillna(0)
    test_slice["strat"] = test_slice["ret"] * pred

    cum_bh = (1+test_slice["ret"]).cumprod()
    cum_strat = (1+test_slice["strat"]).cumprod()

    plt.figure(figsize=(9,5))
    plt.plot(cum_bh.values, label="Buy & Hold", lw=2)
    plt.plot(cum_strat.values, label=f"Strategy (p≥{args.p_up})", lw=2)
    plt.title(f"{args.ticker} — {model_name} Price + Embeddings")
    plt.grid(True); plt.legend(); plt.tight_layout(); plt.show()

# -------------------- CLI --------------------

def main():
    ap = argparse.ArgumentParser(description="News2Signal: scrape, embed, and train trading signal model in one file.")
    sub = ap.add_subparsers(dest="cmd", required=True)

    ap_embed = sub.add_parser("embed", help="Scrape news and write embeddings CSV")
    ap_embed.add_argument("--out", required=True, help="Output embeddings CSV path")
    ap_embed.add_argument("--since", default=None, help="YYYY-MM-DD UTC")
    ap_embed.add_argument("--until", default=None, help="YYYY-MM-DD UTC")
    ap_embed.add_argument("--tickers", nargs="*", default=[], help="Filter tickers (default curated)")
    ap_embed.add_argument("--keywords", nargs="*", default=[], help="Filter keywords (default curated)")
    ap_embed.add_argument("--max_articles", type=int, default=1000)
    ap_embed.add_argument("--use_openai", action="store_true", help="Use OpenAI embeddings")
    ap_embed.add_argument("--openai_model", default="text-embedding-3-small")
    ap_embed.add_argument("--st_model", default="sentence-transformers/all-MiniLM-L6-v2")
    ap_embed.set_defaults(func=cmd_embed)

    ap_train = sub.add_parser("train", help="Merge price+embeddings and train model")
    ap_train.add_argument("--price_csv", required=True)
    ap_train.add_argument("--emb_csv", required=True)
    ap_train.add_argument("--ticker", default="META")
    ap_train.add_argument("--start", default=None)
    ap_train.add_argument("--end", default=None)
    ap_train.add_argument("--p_up", type=float, default=0.60, help="Prob threshold to go long")
    ap_train.set_defaults(func=cmd_train)

    args = ap.parse_args()
    args.func(args)

if __name__ == "__main__":
    main()