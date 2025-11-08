#!/usr/bin/env python3
"""
make_colin_stock.py
-------------------
Build a "colin_stock.csv"-style feature table from raw minute bars (and optional ETF benchmarks).
Computes common technicals + forward targets used by your earlier pipeline.

Inputs:
  --price_csv <path>  minute bars with at least: timestamp,ticker,open,high,low,close,volume
  --etf_spy <path>    (optional) SPY minute bars
  --etf_qqq <path>    (optional) QQQ minute bars
  --out <path>        output CSV

Example:
  python make_colin_stock.py --price_csv meta_minute.csv --etf_spy spy.csv --etf_qqq qqq.csv --out colin_stock.csv

Deps:
  pip install pandas numpy ta
"""

import argparse, math
import pandas as pd, numpy as np

def _read_bars(path):
    df = pd.read_csv(path)
    df["timestamp"] = pd.to_datetime(df["timestamp"], utc=True, errors="coerce")
    df = df.dropna(subset=["timestamp"]).sort_values("timestamp").reset_index(drop=True)
    return df

def _pct_ret(s):
    return s.pct_change()

def compute_indicators(df):
    # Requires columns: open, high, low, close, volume
    out = df.copy()
    # Returns
    out["return_5m"] = out["close"].pct_change().fillna(0.0)
    out["return_15m"] = out["close"].pct_change(3).fillna(0.0)
    out["return_30m"] = out["close"].pct_change(6).fillna(0.0)
    # EMA
    out["ema_9"] = out["close"].ewm(span=9, adjust=False).mean()
    out["ema_12"] = out["close"].ewm(span=12, adjust=False).mean()
    out["ema_26"] = out["close"].ewm(span=26, adjust=False).mean()
    out["ema_50"] = out["close"].ewm(span=50, adjust=False).mean()
    out["price_vs_ema9"] = out["close"]/out["ema_9"] - 1.0
    out["price_vs_ema50"] = out["close"]/out["ema_50"] - 1.0
    # MACD
    out["macd"] = out["ema_12"] - out["ema_26"]
    out["macd_signal"] = out["macd"].ewm(span=9, adjust=False).mean()
    out["macd_hist"] = out["macd"] - out["macd_signal"]
    # RSI
    delta = out["close"].diff()
    up = delta.clip(lower=0).ewm(alpha=1/7, adjust=False).mean()
    down = (-delta.clip(upper=0)).ewm(alpha=1/7, adjust=False).mean()
    rs = up / (down + 1e-12)
    out["rsi_7"] = 100 - (100/(1+rs))
    # Bollinger
    mid = out["close"].rolling(20).mean()
    std = out["close"].rolling(20).std(ddof=0)
    out["bb_mid"] = mid
    out["bb_upper"] = mid + 2*std
    out["bb_lower"] = mid - 2*std
    out["bb_width"] = (out["bb_upper"] - out["bb_lower"]) / out["bb_mid"]
    out["bb_position"] = (out["close"] - out["bb_lower"]) / (out["bb_upper"] - out["bb_lower"] + 1e-12)
    # ATR (normalized)
    tr = np.maximum(out["high"]-out["low"], np.maximum((out["high"]-out["close"].shift()).abs(), (out["low"]-out["close"].shift()).abs()))
    out["atr_14"] = tr.rolling(14).mean()
    out["atr_normalized"] = (out["atr_14"] / out["close"]).fillna(0.0)
    # VWAP (rolling intraday naive approximation)
    pv = out["close"]*out["volume"]
    out["vwap"] = (pv.rolling(20, min_periods=1).sum() / out["volume"].rolling(20, min_periods=1).sum()).fillna(out["close"])
    out["price_vs_vwap"] = out["close"]/out["vwap"] - 1.0
    # Target labels (forward returns)
    out["target_5m_return"] = out["close"].shift(-1).pct_change().shift(0)  # effectively close_{t+1}/close_{t} - 1
    out["target_15m_return"] = out["close"].shift(-3)/out["close"] - 1.0
    out["target_30m_return"] = out["close"].shift(-6)/out["close"] - 1.0
    out["target_up_bin"] = (out["target_15m_return"] > 0).astype(int)
    return out

def add_benchmarks(main_df, etf_df, prefix):
    etf = etf_df[["timestamp","close"]].rename(columns={"close": f"{prefix}_close"}).copy()
    for k in [1,3,6,12]:  # 5m, 15m, 30m, 60m (approx 12)
        etf[f"{prefix}_ret_{k*5}m"] = etf[f"{prefix}_close"].pct_change(k).fillna(0.0)
    merged = pd.merge_asof(main_df.sort_values("timestamp"),
                           etf.sort_values("timestamp"),
                           on="timestamp")
    return merged

def main():
    ap = argparse.ArgumentParser(description="Build colin_stock-style features from raw minute bars.")
    ap.add_argument("--price_csv", required=True, help="Input minute bars CSV for one ticker (timestamp,ticker,open,high,low,close,volume)")
    ap.add_argument("--out", required=True, help="Output CSV path (colin_stock.csv)")
    ap.add_argument("--etf_spy", default=None)
    ap.add_argument("--etf_qqq", default=None)
    ap.add_argument("--etf_dia", default=None)
    ap.add_argument("--etf_iwm", default=None)
    args = ap.parse_args()

    df = _read_bars(args.price_csv)
    if "ticker" not in df.columns:
        df["ticker"] = "TICK"
    feat = compute_indicators(df)

    # optional ETFs
    if args.etf_spy: feat = add_benchmarks(feat, _read_bars(args.etf_spy), "SPY")
    if args.etf_qqq: feat = add_benchmarks(feat, _read_bars(args.etf_qqq), "QQQ")
    if args.etf_dia: feat = add_benchmarks(feat, _read_bars(args.etf_dia), "DIA")
    if args.etf_iwm: feat = add_benchmarks(feat, _read_bars(args.etf_iwm), "IWM")

    feat.to_csv(args.out, index=False)
    print(f"Wrote {len(feat):,} rows to {args.out}")

if __name__ == "__main__":
    main()
