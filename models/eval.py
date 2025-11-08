#!/usr/bin/env python3
"""
Train on first 25 days and evaluate on last 5 days (time-based split)
Show progress with tqdm.
"""

import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import f1_score, classification_report
from xgboost import XGBClassifier
from tqdm import tqdm


# ------------------------
# 1. Load data
# ------------------------
stock_path = "../data/stock_features_google_polygon.csv"
news_path  = "../data/Google_news_embeddings.csv"

stock_df = pd.read_csv(stock_path, parse_dates=["timestamp"])
news_df  = pd.read_csv(news_path, parse_dates=["date"])

stock_df["date"] = stock_df["timestamp"].dt.date
news_df["date"]  = news_df["date"].dt.date

# ------------------------
# 2. Merge
# ------------------------
merged = pd.merge(stock_df, news_df, on=["ticker", "date"], how="left")

emb_cols = [c for c in merged.columns if c.startswith("emb_")]
for c in emb_cols:
    merged[c] = merged[c].fillna(0.0)

merged = merged.dropna(subset=["target_up_bin"])
merged = merged.sort_values("timestamp")

print(f"✅ merged shape = {merged.shape}")
print(f"期間: {merged['date'].min()} → {merged['date'].max()}")

# ------------------------
# 3. 時系列スプリット
# ------------------------
unique_dates = sorted(merged["date"].unique())
split_idx = int(len(unique_dates) * 25 / 30)
train_days = unique_dates[:split_idx]
eval_days  = unique_dates[split_idx:]

train_df = merged[merged["date"].isin(train_days)]
eval_df  = merged[merged["date"].isin(eval_days)]

print(f"Train期間: {train_days[0]} → {train_days[-1]} ({len(train_days)}日)")
print(f"Eval期間:  {eval_days[0]} → {eval_days[-1]} ({len(eval_days)}日)")

# ------------------------
# 4. 特徴量セット
# ------------------------
exclude_cols = [
    "timestamp", "date", "ticker",
    "target_5m_return", "target_up_bin",
    "title", "link", "media"
]
feature_cols = [c for c in merged.columns if c not in exclude_cols]

X_train = train_df[feature_cols].values
y_train = train_df["target_up_bin"].astype(int).values

X_eval = eval_df[feature_cols].values
y_eval = eval_df["target_up_bin"].astype(int).values

y_train = pd.to_numeric(train_df["target_up_bin"], errors="coerce").fillna(0).astype(int)
y_eval  = pd.to_numeric(eval_df["target_up_bin"], errors="coerce").fillna(0).astype(int)

# ------------------------
# 5. NaN処理 + 標準化
# ------------------------
X_train = np.nan_to_num(X_train, nan=0.0, posinf=0.0, neginf=0.0)
X_eval  = np.nan_to_num(X_eval,  nan=0.0, posinf=0.0, neginf=0.0)

scaler = StandardScaler()
X_train = scaler.fit_transform(X_train)
X_eval  = scaler.transform(X_eval)

# ------------------------
# 6. tqdm付きの学習
# ------------------------
model = XGBClassifier(
    n_estimators=300,
    learning_rate=0.05,
    max_depth=6,
    subsample=0.8,
    colsample_bytree=0.8,
    eval_metric="logloss",
    random_state=42,
    verbosity=1,
)

print("🚀 training...")
model.fit(
    X_train, y_train,
    eval_set=[(X_train, "train"), (X_eval, "eval")],
    verbose=True
)

# 評価
y_pred = model.predict(X_eval)
f1 = f1_score(y_eval, y_pred)
print("\n📊 評価結果")
print(f"F1-score: {f1:.4f}")
print(classification_report(y_eval, y_pred, digits=3))