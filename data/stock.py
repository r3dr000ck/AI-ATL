import time
import requests
import pandas as pd
import numpy as np
from datetime import datetime, timezone, timedelta

API_KEY = "dYELOfhzHjpfSx6oHPlBTPF44OVPvt41"
TICKER = "META"
START = "2025-07-15"
END   = "2025-08-15"
OUT_CSV = "meta_stock.csv"
INTERVAL_MINUTES = 5

def ema(series: pd.Series, span: int) -> pd.Series:
    """Exponential Moving Average"""
    return series.ewm(span=span, adjust=False).mean()

def rsi(series: pd.Series, length: int = 14) -> pd.Series:
    """Relative Strength Index"""
    delta = series.diff()
    gain = np.where(delta > 0, delta, 0)
    loss = np.where(delta < 0, -delta, 0)
    roll_up = pd.Series(gain).rolling(length).mean()
    roll_down = pd.Series(loss).rolling(length).mean()
    rs = roll_up / (roll_down + 1e-9)
    return 100 - (100 / (1 + rs))

def macd(series: pd.Series, fast=12, slow=26, signal=9):
    """MACD, Signal, Histogram"""
    ema_fast = ema(series, fast)
    ema_slow = ema(series, slow)
    macd_line = ema_fast - ema_slow
    signal_line = ema(macd_line, signal)
    hist = macd_line - signal_line
    return macd_line, signal_line, hist

def fetch_polygon_bars(ticker: str, start: str, end: str, interval_minutes: int = 5) -> pd.DataFrame:
    url = f"https://api.polygon.io/v2/aggs/ticker/{ticker}/range/{interval_minutes}/minute/{start}/{end}"
    params = {
        "adjusted": "true",
        "sort": "asc",
        "limit": 50000,
        "apiKey": API_KEY
    }
    print(f"Fetching {ticker} {interval_minutes}-min bars {start} → {end} …")
    r = requests.get(url, params=params)
    if r.status_code != 200:
        raise RuntimeError(f"Polygon/Massive error: {r.status_code} {r.text}")
    data = r.json()
    if "results" not in data or not data["results"]:
        print("⚠️ No data returned")
        return pd.DataFrame()
    df = pd.DataFrame(data["results"])
    df.rename(columns={
        "t": "timestamp", "o": "open", "h": "high",
        "l": "low", "c": "close", "v": "volume"
    }, inplace=True)
    df["timestamp"] = pd.to_datetime(df["timestamp"], unit="ms", utc=True)
    df.set_index("timestamp", inplace=True)
    df["ticker"] = ticker
    return df

df = fetch_polygon_bars(TICKER, START, END, INTERVAL_MINUTES)

if df.empty:
    print("❌ No data returned from Polygon/Massive.")

def compute_features(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()

    out["return_5m"] = out["close"].pct_change()
    out["return_30m"] = out["close"].pct_change(6)
    out["return_1h"] = out["close"].pct_change(12)
    out["volatility_1h"] = out["return_5m"].rolling(12, min_periods=8).std()

    # RSI
    out["rsi_14"] = rsi(out["close"], 14)

    # MACD
    out["macd"], out["macd_signal"], out["macd_hist"] = macd(out["close"])

    # EMA
    out["ema_12"] = ema(out["close"], 12)
    out["ema_26"] = ema(out["close"], 26)

    # Relative Volume
    window = 5 * 78
    out["rel_volume"] = out["volume"] / (
        out["volume"].rolling(window, min_periods=78).median()
    )

    return out.dropna(subset=["close"]).copy()

def add_sentiment_placeholders(df: pd.DataFrame) -> pd.DataFrame:
    df["sentiment_score"] = 0.0
    df["reputable_mentions"] = 0
    df["politician_trades"] = 0.0
    df["insider_activity_score"] = 0.0
    df["earnings_sentiment"] = 0.0
    df["google_trend_score"] = np.nan
    return df


def add_labels(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["target_5m_return"] = df["close"].pct_change(periods=-1)
    df["target_up_bin"] = (df["target_5m_return"] > 0.0005).astype(int)
    return df

df_feat = compute_features(df)
df_feat = add_sentiment_placeholders(df_feat)
df_feat = add_labels(df_feat)
df_feat = df_feat.reset_index().rename(columns={"index": "timestamp"})

preferred = [
        "timestamp", "ticker",
        "open", "high", "low", "close", "volume",
        "return_5m", "return_30m", "return_1h", "volatility_1h",
        "rsi_14", "macd", "macd_signal", "macd_hist",
        "ema_12", "ema_26", "rel_volume",
        "sentiment_score", "reputable_mentions", "politician_trades",
        "insider_activity_score", "earnings_sentiment", "google_trend_score",
        "target_5m_return", "target_up_bin"
    ]

cols = [c for c in preferred if c in df_feat.columns]
df_feat = df_feat[cols].sort_values("timestamp").reset_index(drop=True)
df_feat.to_csv(OUT_CSV, index=False)
print(f"✅ Wrote {len(df_feat):,} rows to {OUT_CSV}")
