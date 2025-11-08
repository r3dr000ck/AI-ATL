#!/usr/bin/env python3
"""
embed_news_to_csv.py
--------------------
Scrape reputable sources via RSS, extract article text, embed (OpenAI or SentenceTransformers),
and write embeddings CSV suitable for joining with 5-min bars by timestamp.

Examples:
  # Local embeddings (no API keys):
  python embed_news_to_csv.py --out meta_emb.csv --since 2024-01-01 --until 2024-03-01 --tickers META NVDA

  # OpenAI embeddings:
  export OPENAI_API_KEY=sk-...
  python embed_news_to_csv.py --out meta_emb.csv --since 2024-01-01 --until 2024-03-01 --tickers META --use_openai

Dependencies:
  pip install pandas numpy requests feedparser beautifulsoup4 readability-lxml langdetect sentence-transformers
  # optional for OpenAI: pip install openai
"""

import os, re, argparse, sys
import pandas as pd, numpy as np
import requests, feedparser
from typing import List, Dict, Optional
from dataclasses import dataclass
from bs4 import BeautifulSoup
from langdetect import detect as lang_detect

try:
    from readability import Document  # from readability-lxml
except Exception:
    Document = None

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
    # readability-lxml preferred
    if Document is not None:
        try:
            doc = Document(html)
            content_html = doc.summary()
            soup = BeautifulSoup(content_html, "html.parser")
            txt = clean_text(soup.get_text(separator=" "))
            if len(txt) > 200:
                return txt
        except Exception:
            pass
    # fallback: heuristic strip
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
        try:
            from openai import OpenAI
        except Exception as e:
            raise RuntimeError("OpenAI SDK not installed. pip install openai") from e
        client = OpenAI()
        out = []
        for t in texts:
            t = t[:7000]  # safety
            resp = client.embeddings.create(model=openai_model, input=t)
            out.append(resp.data[0].embedding)
        return np.array(out, dtype=float)
    else:
        try:
            from sentence_transformers import SentenceTransformer
        except Exception as e:
            raise RuntimeError("sentence-transformers not installed. pip install sentence-transformers") from e
        model = SentenceTransformer(st_model_name)
        return model.encode(texts, normalize_embeddings=False)

def main():
    ap = argparse.ArgumentParser(description="Fetch news, embed, and write CSV for joining with price bars.")
    ap.add_argument("--out", required=True, help="Output embeddings CSV path")
    ap.add_argument("--since", default=None, help="YYYY-MM-DD UTC")
    ap.add_argument("--until", default=None, help="YYYY-MM-DD UTC")
    ap.add_argument("--tickers", nargs="*", default=[], help="Filter tickers (default curated)")
    ap.add_argument("--keywords", nargs="*", default=[], help="Filter keywords (default curated)")
    ap.add_argument("--max_articles", type=int, default=1000)
    ap.add_argument("--use_openai", action="store_true", help="Use OpenAI embeddings (requires OPENAI_API_KEY)")
    ap.add_argument("--openai_model", default="text-embedding-3-small")
    ap.add_argument("--st_model", default="sentence-transformers/all-MiniLM-L6-v2")
    args = ap.parse_args()

    sources = [Source(**s) for s in DEFAULT_SOURCES]
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
        print("No entries found."); sys.exit(0)

    df["date"] = pd.to_datetime(df["date"], utc=True, errors="coerce")
    df = df.dropna(subset=["date"]).sort_values("date")
    if args.since:
        df = df[df["date"] >= pd.Timestamp(args.since, tz="UTC")]
    if args.until:
        df = df[df["date"] <= pd.Timestamp(args.until, tz="UTC")]

    tickers = args.tickers or DEFAULT_TICKERS
    keywords = args.keywords or DEFAULT_KEYWORDS
    if tickers or keywords:
        mask = df.apply(lambda r: filter_by_keywords(r, tickers, keywords), axis=1)
        df = df[mask]

    df = df.drop_duplicates(subset=["url"], keep="last")
    if df.empty:
        print("No entries after filters."); sys.exit(0)

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
            "source": r.get("source","")
        })
        texts.append(text)

    if not rows:
        print("No parsed articles."); sys.exit(0)

    embs = build_embeddings(texts, use_openai=args.use_openai, openai_model=args.openai_model, st_model_name=args.st_model)
    dim = embs.shape[1]
    out_df = pd.DataFrame(rows)
    for j in range(dim):
        out_df[f"emb_{j}"] = embs[:, j]
    cols = ["title","date","url","country","language","source"] + [f"emb_{j}" for j in range(dim)]
    out_df = out_df[cols]
    out_df.to_csv(args.out, index=False, encoding="utf-8")
    print(f"Wrote {len(out_df)} rows with {dim}-dim embeddings to {args.out}")

if __name__ == "__main__":
    main()
