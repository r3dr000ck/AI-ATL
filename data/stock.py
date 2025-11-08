#!/usr/bin/env python3
"""
stock.py
---------
Download minute bars from Polygon.io, compute technical indicators & features,
and export a ready-to-train CSV dataset.

Usage:
    python3 ./data/stock.py download META \
        --start 2025-07-01 --end 2025-07-31 \
        --out ../data/meta-july.csv
"""

import argparse, os, time, requests
import pandas as pd, numpy as np

# ====== CONFIG ======
API_KEY = "dYELOfhzHjpfSx6oHPlBTPF44OVPvt41"
INTERVAL_MINUTES = 5
# ====================

# ====== META INFO ======
STOCK_INFO = {
    'META': {'sector':'Communication Services','market_cap':'mega','is_tech':1,'is_faang':1,'is_mag7':1},
    'AAPL': {'sector':'Information Technology','market_cap':'mega','is_tech':1,'is_faang':1,'is_mag7':1},
    'GOOGL': {'sector':'Communication Services','market_cap':'mega','is_tech':1,'is_faang':1,'is_mag7':1},
    'AMZN': {'sector':'Consumer Discretionary','market_cap':'mega','is_tech':1,'is_faang':1,'is_mag7':1},
    'NVDA': {'sector':'Information Technology','market_cap':'mega','is_tech':1,'is_faang':0,'is_mag7':1},
    'MSFT': {'sector':'Information Technology','market_cap':'mega','is_tech':1,'is_faang':0,'is_mag7':1},
    'TSLA': {'sector':'Consumer Discretionary','market_cap':'mega','is_tech':1,'is_faang':0,'is_mag7':1},
}
# =======================

# ====== INDICATORS ======
def ema(s, span): return s.ewm(span=span, adjust=False).mean()
def rsi(series, length=14):
    d = series.diff()
    up, dn = np.where(d>0,d,0.0), np.where(d<0,-d,0.0)
    roll_up = pd.Series(up,index=series.index).rolling(length,min_periods=length//2).mean()
    roll_dn = pd.Series(dn,index=series.index).rolling(length,min_periods=length//2).mean()
    rs = roll_up/(roll_dn+1e-12)
    return 100 - (100/(1+rs))
def macd(series, fast=12, slow=26, signal=9):
    f, sl = ema(series,fast), ema(series,slow)
    line = f - sl; sig = ema(line,signal)
    return line, sig, line - sig
def atr(h,l,c,length=14):
    tr = pd.concat([(h-l),(h-c.shift()).abs(),(l-c.shift()).abs()],axis=1).max(axis=1)
    return tr.rolling(length,min_periods=length//2).mean()
def bollinger(series,length=20,std=2.0):
    sma = series.rolling(length,min_periods=length//2).mean()
    sdev = series.rolling(length,min_periods=length//2).std()
    return sma+std*sdev, sma, sma-std*sdev
# ==========================

def fetch_polygon_bars(ticker, start, end, interval_minutes=5, retries=3):
    url = f"https://api.polygon.io/v2/aggs/ticker/{ticker}/range/{interval_minutes}/minute/{start}/{end}"
    params = {"adjusted":"true","sort":"asc","limit":50000,"apiKey":API_KEY}
    for a in range(retries):
        try:
            r = requests.get(url, params=params, timeout=30)
            if r.status_code == 429: time.sleep(60*(a+1)); continue
            r.raise_for_status()
            data = r.json()
            if not data.get("results"): return pd.DataFrame()
            df = pd.DataFrame(data["results"]).rename(columns={
                "t":"timestamp","o":"open","h":"high","l":"low","c":"close","v":"volume","vw":"vwap","n":"trades"
            })
            df["timestamp"] = pd.to_datetime(df["timestamp"],unit="ms",utc=True)
            df = df.set_index("timestamp").sort_index()
            df["ticker"] = ticker
            return df
        except Exception as e:
            print(f"[WARN] retry {a+1}/{retries}: {e}")
            time.sleep(2**a)
    return pd.DataFrame()

# ====== FEATURE ENGINEERING ======
def compute_core_features(df):
    out = df.copy()
    out["return_5m"] = out["close"].pct_change()
    out["return_15m"] = out["close"].pct_change(3)
    out["return_30m"] = out["close"].pct_change(6)
    out["return_1h"] = out["close"].pct_change(12)
    out["return_4h"] = out["close"].pct_change(48)
    out["volatility_30m"] = out["return_5m"].rolling(6).std()
    out["volatility_1h"]  = out["return_5m"].rolling(12).std()
    out["volatility_4h"]  = out["return_5m"].rolling(48).std()
    out["rsi_7"],out["rsi_14"],out["rsi_21"] = rsi(out["close"],7),rsi(out["close"],14),rsi(out["close"],21)
    out["macd"],out["macd_signal"],out["macd_hist"] = macd(out["close"])
    for s in [9,12,26,50]: out[f"ema_{s}"]=ema(out["close"],s)
    out["price_vs_ema9"]=(out["close"]-out["ema_9"])/out["ema_9"]
    out["price_vs_ema50"]=(out["close"]-out["ema_50"])/out["ema_50"]
    out["atr_14"]=atr(out["high"],out["low"],out["close"],14)
    out["atr_normalized"]=out["atr_14"]/out["close"]
    u,m,l=bollinger(out["close"],20,2.0)
    out["bb_upper"],out["bb_mid"],out["bb_lower"]=u,m,l
    out["bb_width"]=(u-l)/m.replace(0,np.nan)
    out["bb_position"]=(out["close"]-l)/(u-l)
    return out

def add_stock_classification(df,ticker):
    info=STOCK_INFO.get(ticker,{'sector':'Unknown','market_cap':'large','is_tech':0,'is_faang':0,'is_mag7':0})
    df["is_tech_stock"]=info['is_tech']; df["is_faang"]=info['is_faang']; df["is_mag7"]=info['is_mag7']
    df["market_cap_mega"]=1 if info['market_cap']=="mega" else 0
    sec=info['sector']
    df["sector_technology"]=int("Technology" in sec)
    df["sector_consumer"]=int("Consumer" in sec)
    df["sector_healthcare"]=int("Health" in sec)
    df["sector_financial"]=int("Financial" in sec)
    return df

def add_time_features(df):
    et=df.index.tz_convert("America/New_York")
    df["hour"]=et.hour; df["minute"]=et.minute; df["day_of_week"]=et.dayofweek
    df["hour_sin"]=np.sin(2*np.pi*(et.hour+et.minute/60)/24)
    df["hour_cos"]=np.cos(2*np.pi*(et.hour+et.minute/60)/24)
    return df

def add_labels(df,threshold=0.0005):
    out=df.copy()
    out["target_5m_return"]=out["close"].pct_change(-1)
    out["target_up_bin"]=(out["target_5m_return"]>threshold).astype(int)
    return out

# ====== MAIN PIPELINE ======
def run_download(ticker,start,end,out_csv):
    print(f"\n=== Building feature dataset for {ticker} ({start} → {end}) ===")
    df=fetch_polygon_bars(ticker,start,end,INTERVAL_MINUTES)
    if df.empty:
        print("❌ No data fetched."); return
    print(f"✓ Bars fetched: {len(df):,}")

    feat=compute_core_features(df)
    feat=add_stock_classification(feat,ticker)
    feat=add_time_features(feat)
    feat=add_labels(feat)
    feat=feat.iloc[:-1].reset_index()

    # ✅ create parent directory automatically
    os.makedirs(os.path.dirname(out_csv), exist_ok=True)
    feat.to_csv(out_csv,index=False)
    print(f"✅ Wrote {len(feat):,} rows × {len(feat.columns)} cols → {out_csv}")

# ====== CLI ======
def main():
    parser=argparse.ArgumentParser(description="Stock Feature Builder CLI")
    sub=parser.add_subparsers(dest="cmd")

    dl=sub.add_parser("download",help="Download & feature-engineer stock data")
    dl.add_argument("ticker",type=str)
    dl.add_argument("--start",required=True)
    dl.add_argument("--end",required=True)
    dl.add_argument("--out",required=True)

    args=parser.parse_args()
    if args.cmd=="download":
        run_download(args.ticker.upper(),args.start,args.end,args.out)
    else:
        parser.print_help()

if __name__=="__main__":
    main()
