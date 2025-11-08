#!/usr/bin/env python3
"""
gemini_1.py — robust stage-1 summarizer with root-cause diagnostics

- Loads last N rows for TICKER
- Builds a compact, safe payload (few numeric arrays + tiny stats, <= 4KB)
- Asks Gemini for a neutral plain-text summary (no advice)
- Triple-fallback if first attempt returns no text
- Writes summary.txt, summary.json (payload), and summary_diag.json (diagnostics)

Requirements: pip install google-generativeai pandas numpy
Environment: export GEMINI_API_KEY=YOUR_API_KEY
"""

import os, json
import numpy as np
import pandas as pd
import google.generativeai as genai

# ===== CONFIG =====
CSV_PATH   = "../data/meta-july.csv"
TICKER     = "META"
N_LAST     = 24
MODEL      = "models/gemini-2.5-flash"   # more tolerant than flash
TEMP       = 0.1
OUT_TXT    = "summary.txt"
OUT_JSON   = "summary.json"            # payload actually sent (first attempt)
OUT_DIAG   = "summary_diag.json"       # diagnostics log
MAX_PROMPT_CHARS = 4000                # hard cap for text fed to LLM

GEMINI_API_KEY = "AIzaSyAguY8tFf8snXyFHUsGFlE8BqMOdy1Nwr8"

# ==================

def load_df():
    df = pd.read_csv(CSV_PATH)
    if "timestamp" in df.columns:
        df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce")
    if "ticker" in df.columns:
        if TICKER not in set(df["ticker"]):
            raise SystemExit(f"❌ TICKER '{TICKER}' not found in CSV. Found: {sorted(df['ticker'].unique())[:10]} ...")
        df = df[df["ticker"] == TICKER]
    if df.empty:
        raise SystemExit("❌ After filtering, DataFrame is empty.")
    df = df.sort_values("timestamp" if "timestamp" in df.columns else df.columns[0]).reset_index(drop=True)
    tail = df.tail(N_LAST).copy()
    if tail.empty:
        raise SystemExit(f"❌ Not enough rows for last {N_LAST}.")
    return tail

def select_numeric(df):
    # Preferred set; fallback to top-variance numeric columns
    preferred = ["close","return_5m","return_15m","rsi_7","macd_hist","price_vs_vwap","atr_normalized","volume"]
    cols = [c for c in preferred if c in df.columns]
    if not cols:
        num = df.select_dtypes(include=[np.number])
        if num.shape[1] == 0:
            raise SystemExit("❌ No numeric columns available in the CSV.")
        cols = list(num.var().sort_values(ascending=False).index[:4])
    # Cap to 4 columns to keep context small & safe
    return cols[:4], df[cols[:4]].copy()

def qarr(series, nd=4):
    s = pd.to_numeric(series, errors="coerce")
    return [None if pd.isna(v) else float(np.round(v, nd)) for v in s.tolist()]

def build_payload(df):
    cols, num = select_numeric(df)
    rows = {}
    stats = {}
    for c in cols:
        arr = pd.to_numeric(num[c], errors="coerce")
        rows[c] = qarr(arr)
        if arr.notna().sum() == 0:
            raise SystemExit(f"❌ Column '{c}' has only NaN in the selected window.")
        stats[c] = {
            "mean": float(np.nanmean(arr)),
            "std":  float(np.nanstd(arr)),
            "min":  float(np.nanmin(arr)),
            "max":  float(np.nanmax(arr)),
            "last": float(arr.iloc[-1])
        }
    payload = {
        "ticker": TICKER,
        "window": int(len(num)),
        "columns": cols,
        "rows": rows,   # {col: [v1,...]}
        "stats": stats
    }
    return payload

def prompt_for_summary(payload):
    # Keep wording neutral & compact; avoid “financial/advice”.
    body = json.dumps(payload, ensure_ascii=False)
    
    if len(body) > MAX_PROMPT_CHARS:
        body = body[:MAX_PROMPT_CHARS] + " ... (truncated)"
    return (
        "You will receive a small data snippet containing a few short arrays and brief stats.\n"
        "Describe the recent movement patterns in 4–6 short bullet points:\n"
        "- whether values appear to be rising, falling, or steady overall\n"
        "- whether changes seem to accelerate or flatten\n"
        "- whether the series looks choppy or calm\n"
        "- any note about alignment between arrays and stats\n\n"
        "Keep it concise and neutral; return plain text only.\n\n"
        f"Data:\n{body}"
    )

def _extract_text(resp):
    # まず、candidatesが存在するか確認
    if not hasattr(resp, "candidates") or not resp.candidates:
        return "", "NO_CANDIDATE", 0

    cand = resp.candidates[0]
    
    # finish_reasonを取得し、名前（文字列）に変換
    finish = cand.finish_reason.name if hasattr(cand.finish_reason, 'name') else str(cand.finish_reason)
    
    # contentが存在するか確認
    content = getattr(cand, "content", None)
    if not content:
        return "", finish, 0
    
    # partsからテキストを抽出
    parts = getattr(content, "parts", [])
    text = "".join(getattr(p, "text", "") for p in parts).strip()
    
    return text, finish, len(parts)

def call_gemini(prompt, mini=None, tiny=None):
    key = GEMINI_API_KEY
    if not key:
        raise SystemExit("❌ GEMINI_API_KEY not set.")
    genai.configure(api_key=key)
    model = genai.GenerativeModel(MODEL)

    diag = {"attempts": []}

    # Attempt 1: full compact payload
    resp1 = model.generate_content(
        prompt,
        generation_config=genai.types.GenerationConfig(
            temperature=TEMP,
            max_output_tokens=5000,
            response_mime_type="text/plain"
        ),
        safety_settings=[
            {"category":"HARM_CATEGORY_DANGEROUS_CONTENT","threshold":"BLOCK_NONE"},
            {"category":"HARM_CATEGORY_HARASSMENT","threshold":"BLOCK_NONE"},
            {"category":"HARM_CATEGORY_HATE_SPEECH","threshold":"BLOCK_NONE"},
            {"category":"HARM_CATEGORY_SEXUALLY_EXPLICIT","threshold":"BLOCK_NONE"},
        ],
    )
    
    # print(resp1)
    
    text1, finish1, parts1 = _extract_text(resp1)
    diag["attempts"].append({"which":"full", "finish_reason": finish1, "parts": parts1, "len(text)": len(text1)})

    if text1:
        return text1, diag

    # Attempt 2: mini payload (single column)
    if mini:
        p2 = prompt_for_summary(mini)
        resp2 = model.generate_content(
            p2,
            generation_config=genai.types.GenerationConfig(
                temperature=TEMP, max_output_tokens=400, response_mime_type="text/plain"
            ),
        )
        text2, finish2, parts2 = _extract_text(resp2)
        diag["attempts"].append({"which":"mini", "finish_reason": finish2, "parts": parts2, "len(text)": len(text2)})
        if text2:
            return text2, diag

    # Attempt 3: ultra-tiny prompt = one short numeric list
    if tiny:
        p3 = (
            f"Here is a short list of values: {tiny}\n"
            "Write 3 short bullets describing whether they seem to rise, fall, or stay steady; "
            "mention if changes look choppy or calm. Plain text only."
        )
        resp3 = model.generate_content(
            p3,
            generation_config=genai.types.GenerationConfig(
                temperature=TEMP, max_output_tokens=200, response_mime_type="text/plain"
            ),
        )
        text3, finish3, parts3 = _extract_text(resp3)
        diag["attempts"].append({"which":"tiny", "finish_reason": finish3, "parts": parts3, "len(text)": len(text3)})
        if text3:
            return text3, diag

    return "", diag

def main():
    df = load_df()
    payload = build_payload(df)
    
    # print(payload)

    # Prepare fallback mini/tiny variants
    cols = payload["columns"]
    only = cols[0]
    mini = {
        "ticker": payload["ticker"],
        "window": payload["window"],
        "columns": [only],
        "rows": {only: payload["rows"][only]},
        "stats": {only: payload["stats"][only]}
    }
    # Tiny = just the last column list (shortened to 10 values)
    tiny_vals = payload["rows"][only]
    tiny_vals = [v for v in tiny_vals if v is not None][-10:]  # last 10 non-nulls

    prompt = prompt_for_summary(payload)
    
    text, diag = call_gemini(prompt, mini=mini, tiny=tiny_vals)
    
    # Save payload, summary, and diagnostics
    with open(OUT_JSON, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)
    with open(OUT_TXT, "w", encoding="utf-8") as f:
        f.write(text if text else "No summary available.")
    with open(OUT_DIAG, "w", encoding="utf-8") as f:
        json.dump(diag, f, ensure_ascii=False, indent=2)

    print("=== SUMMARY ===")
    print(text if text else "No summary available.")
    print(f"\nSaved: {OUT_TXT}, {OUT_JSON}, {OUT_DIAG}")

if __name__ == "__main__":
    main()
