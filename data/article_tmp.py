#!/usr/bin/env python3
"""
Fetch Meta news from GDELT (robust version).
Handles empty/HTML responses, loops monthly, and saves embeddings to CSV.
"""

import requests
import pandas as pd
import numpy as np
from tqdm import tqdm
from datetime import datetime, timedelta
from sentence_transformers import SentenceTransformer

QUERY = "Meta"
START_DATE = "2024-01-01"
END_DATE   = "2025-01-01"
OUT_CSV    = f"{QUERY.lower()}_emb.csv"

# ------------------------
# Helper: build month ranges
# ------------------------
def month_range(start, end):
    start_dt = datetime.strptime(start, "%Y-%m-%d")
    end_dt = datetime.strptime(end, "%Y-%m-%d")
    months = []
    while start_dt < end_dt:
        next_m = (start_dt.replace(day=28) + timedelta(days=4)).replace(day=1)
        months.append((start_dt.strftime("%Y%m%d%H%M%S"), (next_m - timedelta(days=1)).strftime("%Y%m%d%H%M%S")))
        start_dt = next_m
    return months

# ------------------------
# Fetch from GDELT
# ------------------------
def fetch_gdelt_news(query, start_dt, end_dt, max_records=250):
    url = (
        "https://api.gdeltproject.org/api/v2/doc/doc?"
        f"query={query}&mode=ArtList&maxrecords={max_records}&sort=DateDesc&format=json"
        f"&startdatetime={start_dt}&enddatetime={end_dt}"
    )
    try:
        r = requests.get(url, timeout=20)
        r.raise_for_status()
        try:
            data = r.json()
        except Exception:
            print(f"⚠️ Non-JSON response for {start_dt}→{end_dt}, skipping.")
            return pd.DataFrame()
        if "articles" not in data or not data["articles"]:
            return pd.DataFrame()
        return pd.DataFrame(data["articles"])
    except Exception as e:
        print(f"⚠️ Error fetching {start_dt}→{end_dt}: {e}")
        return pd.DataFrame()

# ------------------------
# Loop monthly and combine
# ------------------------
print(f"Fetching '{QUERY}' news from {START_DATE} to {END_DATE} via GDELT...")
ranges = month_range(START_DATE, END_DATE)
dfs = []
for s, e in tqdm(ranges):
    df_m = fetch_gdelt_news(QUERY, s, e)
    if not df_m.empty:
        dfs.append(df_m)

if not dfs:
    print("⚠️ No data retrieved at all.")
    exit()

df = pd.concat(dfs, ignore_index=True)
df = df.drop_duplicates(subset=["title"]).dropna(subset=["title"])
print(f"✅ Collected {len(df)} unique articles.")

# ------------------------
# Clean and embed
# ------------------------
keep_cols = ["title", "seendate", "url", "sourceCountry", "language"]
for c in keep_cols:
    if c not in df.columns:
        df[c] = np.nan
df = df[keep_cols].rename(columns={"seendate": "date", "sourceCountry": "country"})

print("🔎 Embedding titles with SentenceTransformer...")
model = SentenceTransformer("all-MiniLM-L6-v2")
texts = df["title"].fillna("").tolist()
embeddings = model.encode(texts, show_progress_bar=True)

emb_cols = [f"emb_{i}" for i in range(embeddings.shape[1])]
emb_df = pd.DataFrame(embeddings, columns=emb_cols)
final_df = pd.concat([df.reset_index(drop=True), emb_df], axis=1)

final_df.to_csv(OUT_CSV, index=False)
print(f"✅ Saved {len(final_df)} articles with embeddings to {OUT_CSV}")
