from GoogleNews import GoogleNews
import pandas as pd
from sentence_transformers import SentenceTransformer
import numpy as np
from datetime import datetime, timedelta, timezone
import re

# ------------------------
# Hyperparameters
# ------------------------

QUERY = "Google"
START_DATE = "06/15/2024"
END_DATE = "07/15/2024"
OUT_CSV = f"{QUERY}_news_embeddings.csv"

# ------------------------
# Functions
# ------------------------

def clean_datestr(s: str) -> datetime | None:
    if not isinstance(s, str):
        return None
    s = s.strip()
    now = datetime.now(timezone.utc)
    if "hour" in s:
        m = re.search(r"(\d+)\s*hour", s)
        if m:
            return now - timedelta(hours=int(m.group(1)))
    if "day" in s:
        m = re.search(r"(\d+)\s*day", s)
        if m:
            return now - timedelta(days=int(m.group(1)))
    if "week" in s:
        m = re.search(r"(\d+)\s*week", s)
        if m:
            return now - timedelta(weeks=int(m.group(1)))
    if "month" in s:
        m = re.search(r"(\d+)\s*month", s)
        if m:
            return now - timedelta(days=30 * int(m.group(1)))
    try:
        return pd.to_datetime(s)
    except Exception:
        return None

# ------------------------
# Data Fetching
# ------------------------

print(f"Fetching '{QUERY}' news from {START_DATE} to {END_DATE}...")

googlenews = GoogleNews(lang='en', start=START_DATE, end=END_DATE)
googlenews.search(QUERY)

results = []
for page in range(1, 6):
    googlenews.getpage(page)
    res = googlenews.result()
    results.extend(res)

df = pd.DataFrame(results)
if df.empty:
    print("⚠️ No articles found. Try expanding date range or query.")
    exit()

df = df.drop_duplicates(subset=["title"]).dropna(subset=["title"])
print(f"✅ Collected {len(df)} raw articles.")

# ------------------------
# Embedding Generation
# ------------------------

print("Embedding article titles using SentenceTransformer...")
model = SentenceTransformer("all-MiniLM-L6-v2")
embeddings = model.encode(df["title"].tolist(), show_progress_bar=True)
embeddings = np.array(embeddings)

emb_cols = [f"emb_{i}" for i in range(embeddings.shape[1])]
emb_df = pd.DataFrame(embeddings, columns=emb_cols)

# ------------------------
# Output
# ------------------------

df["parsed_date"] = df["date"].apply(clean_datestr)
merged = pd.concat([df.reset_index(drop=True), emb_df], axis=1)

merged = merged.dropna(subset=["parsed_date"]).copy()
merged["date"] = pd.to_datetime(merged["parsed_date"]).dt.date
merged["ticker"] = "GOOG"

cols_to_keep = ["ticker", "date", "title", "link", "media"] + emb_cols
merged = merged[cols_to_keep].sort_values("date").reset_index(drop=True)

merged.to_csv(OUT_CSV, index=False)
print(f"✅ Saved {len(merged)} articles with embeddings to {OUT_CSV}")
