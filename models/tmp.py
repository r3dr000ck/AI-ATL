#!/usr/bin/env python3
"""
LSTM regression model to predict next 5-minute return (target_5m_return)
using stock_features_google_polygon.csv (+ optional news embeddings).
"""

import torch
import torch.nn as nn
import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import mean_squared_error, mean_absolute_error
from torch.utils.data import Dataset, DataLoader
from tqdm import tqdm

# ------------------------
# Hyperparameters
# ------------------------
SEQ_LEN = 24       # 過去24本（=2時間分）で次の5分を予測
BATCH_SIZE = 64
EPOCHS = 20
LR = 1e-3
DEVICE = "cuda" if torch.cuda.is_available() else "cpu"

stock_path = "../data/meta_stock.csv"

# ------------------------
# Load and preprocess
# ------------------------
df = pd.read_csv(stock_path, parse_dates=["timestamp"])
df = df.sort_values("timestamp")

# target_5m_return がない場合は生成
if "target_5m_return" not in df.columns:
    df["target_5m_return"] = df["close"].pct_change(periods=-1)

df = df.dropna(subset=["target_5m_return"]).reset_index(drop=True)

# 不要列除外
exclude_cols = [
    "timestamp", "ticker", "target_up_bin",  # ← 分類ラベルは使わない
    "sentiment_score", "reputable_mentions", "politician_trades",
    "insider_activity_score", "earnings_sentiment", "google_trend_score"
]
feature_cols = [c for c in df.columns if c not in exclude_cols + ["target_5m_return"]]

# 特徴量スケーリング
df[feature_cols] = df[feature_cols].fillna(0).replace([np.inf, -np.inf], 0)
scaler = StandardScaler()
df[feature_cols] = scaler.fit_transform(df[feature_cols])

# ------------------------
# Dataset
# ------------------------
class StockDataset(Dataset):
    def __init__(self, df, seq_len=24):
        self.X = df[feature_cols].values
        self.y = df["target_5m_return"].values
        self.seq_len = seq_len
    def __len__(self):
        return len(self.X) - self.seq_len - 1
    def __getitem__(self, idx):
        x_seq = self.X[idx:idx+self.seq_len]
        y = self.y[idx+self.seq_len]
        return torch.tensor(x_seq, dtype=torch.float32), torch.tensor(y, dtype=torch.float32)

dataset = StockDataset(df, SEQ_LEN)
train_size = int(len(dataset)*0.8)
train_ds, val_ds = torch.utils.data.random_split(dataset, [train_size, len(dataset)-train_size])
train_dl = DataLoader(train_ds, batch_size=BATCH_SIZE, shuffle=True)
val_dl   = DataLoader(val_ds, batch_size=BATCH_SIZE, shuffle=False)

# ------------------------
# LSTM regression model
# ------------------------
class StockLSTMReg(nn.Module):
    def __init__(self, input_dim, hidden_dim=128):
        super().__init__()
        self.lstm = nn.LSTM(input_dim, hidden_dim, batch_first=True)
        self.fc = nn.Sequential(
            nn.Linear(hidden_dim, 64),
            nn.ReLU(),
            nn.Linear(64, 1)
        )
    def forward(self, x):
        _, (h, _) = self.lstm(x)
        h = h[-1]
        return self.fc(h).squeeze(1)

model = StockLSTMReg(input_dim=len(feature_cols)).to(DEVICE)
criterion = nn.MSELoss()
optimizer = torch.optim.Adam(model.parameters(), lr=LR)

# ------------------------
# Training loop
# ------------------------
print(f"🚀 Training regression on {DEVICE} ...")
for epoch in range(EPOCHS):
    model.train()
    total_loss = 0
    for xb, yb in tqdm(train_dl, desc=f"Epoch {epoch+1}/{EPOCHS}", ncols=100):
        xb, yb = xb.to(DEVICE), yb.to(DEVICE)
        optimizer.zero_grad()
        out = model(xb)
        loss = criterion(out, yb)
        loss.backward()
        optimizer.step()
        total_loss += loss.item()

    # Validation
    model.eval()
    preds, labels = [], []
    with torch.no_grad():
        for xb, yb in val_dl:
            xb, yb = xb.to(DEVICE), yb.to(DEVICE)
            out = model(xb)
            preds += out.cpu().tolist()
            labels += yb.cpu().tolist()

    preds, labels = np.array(preds), np.array(labels)
    mse = mean_squared_error(labels, preds)
    mae = mean_absolute_error(labels, preds)
    corr = np.corrcoef(labels, preds)[0, 1]
    dir_acc = np.mean(np.sign(preds) == np.sign(labels))

    print(f"Epoch {epoch+1}: loss={total_loss/len(train_dl):.6f}, "f"MSE={mse:.6f}, MAE={mae:.6f}, Corr={corr:.3f}, DirAcc={dir_acc:.3f}")

print("✅ Training done.")
