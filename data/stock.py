import time
import requests
import pandas as pd
import numpy as np
from datetime import datetime, timezone, timedelta

API_KEY = "dYELOfhzHjpfSx6oHPlBTPF44OVPvt41"
TICKER = "META"
START = "2024-01-01"
END   = "2025-01-01"
OUT_CSV = "colin_stock.csv"
INTERVAL_MINUTES = 5

# GICS-aligned sector info (simplified)
STOCK_INFO = {
    'META': {'sector':'Communication Services','industry':'Interactive Media & Services','category':'FAANG','market_cap':'mega','is_tech':1,'is_faang':1,'is_mag7':1},
    'AAPL': {'sector':'Information Technology','industry':'Consumer Electronics','category':'FAANG','market_cap':'mega','is_tech':1,'is_faang':1,'is_mag7':1},
    'GOOGL': {'sector':'Communication Services','industry':'Interactive Media & Services','category':'FAANG','market_cap':'mega','is_tech':1,'is_faang':1,'is_mag7':1},
    'AMZN': {'sector':'Consumer Discretionary','industry':'Internet & Direct Marketing Retail','category':'FAANG','market_cap':'mega','is_tech':1,'is_faang':1,'is_mag7':1},
    'NVDA': {'sector':'Information Technology','industry':'Semiconductors','category':'Mega Tech','market_cap':'mega','is_tech':1,'is_faang':0,'is_mag7':1},
    'MSFT': {'sector':'Information Technology','industry':'Software','category':'Mega Tech','market_cap':'mega','is_tech':1,'is_faang':0,'is_mag7':1},
    'TSLA': {'sector':'Consumer Discretionary','industry':'Automobiles','category':'Mega Tech','market_cap':'mega','is_tech':1,'is_faang':0,'is_mag7':1},
}

ETF_BENCHMARKS = {
    'SPY':'S&P 500 ETF', 'QQQ':'Nasdaq-100 ETF', 'DIA':'Dow Jones ETF',
    'IWM':'Russell 2000 ETF', 'XLK':'Tech Sector ETF', 'XLC':'Comm Services ETF', 'VGT':'Vanguard Tech ETF'
}

# ================== INDICATORS ==================
def ema(s: pd.Series, span: int) -> pd.Series:
    return s.ewm(span=span, adjust=False).mean()

def rsi(series: pd.Series, length: int = 14) -> pd.Series:
    d = series.diff()
    up = np.where(d > 0, d, 0.0); dn = np.where(d < 0, -d, 0.0)
    roll_up = pd.Series(up, index=series.index).rolling(length, min_periods=length//2).mean()
    roll_dn = pd.Series(dn, index=series.index).rolling(length, min_periods=length//2).mean()
    rs = roll_up / (roll_dn + 1e-12)
    return 100 - (100 / (1 + rs))

def macd(series: pd.Series, fast=12, slow=26, signal=9):
    f = ema(series, fast); sl = ema(series, slow)
    line = f - sl; sig = ema(line, signal); hist = line - sig
    return line, sig, hist

def atr(h: pd.Series, l: pd.Series, c: pd.Series, length: int = 14):
    tr = pd.concat([(h-l), (h-c.shift()).abs(), (l-c.shift()).abs()], axis=1).max(axis=1)
    return tr.rolling(length, min_periods=length//2).mean()

def bollinger(series: pd.Series, length=20, std=2.0):
    sma = series.rolling(length, min_periods=length//2).mean()
    sdev = series.rolling(length, min_periods=length//2).std()
    upper = sma + std*sdev; lower = sma - std*sdev
    return upper, sma, lower

# ================== DATA ==================
def fetch_polygon_bars(ticker: str, start: str, end: str, interval_minutes=5, retries=3) -> pd.DataFrame:
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
            df["timestamp"] = pd.to_datetime(df["timestamp"], unit="ms", utc=True)
            df = df.set_index("timestamp").sort_index()
            df["ticker"] = ticker
            return df
        except Exception as e:
            if a == retries-1: print(f"[ERROR] {ticker}: {e}"); return pd.DataFrame()
            time.sleep(2**a)
    return pd.DataFrame()

def fetch_multiple_tickers(tickers: list[str], start: str, end: str, interval_minutes=5) -> dict[str, pd.DataFrame]:
    out = {}
    for t in tickers:
        d = fetch_polygon_bars(t, start, end, interval_minutes)
        if not d.empty: out[t] = d
        time.sleep(0.15)
    return out

# ================== FEATURES ==================
def compute_core_features(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    # returns & vols
    out["return_5m"] = out["close"].pct_change()
    out["return_15m"] = out["close"].pct_change(3)
    out["return_30m"] = out["close"].pct_change(6)
    out["return_1h"] = out["close"].pct_change(12)
    out["return_4h"] = out["close"].pct_change(48)
    out["volatility_30m"] = out["return_5m"].rolling(6, min_periods=4).std()
    out["volatility_1h"]  = out["return_5m"].rolling(12, min_periods=8).std()
    out["volatility_4h"]  = out["return_5m"].rolling(48, min_periods=24).std()
    # indicators
    out["rsi_7"] = rsi(out["close"], 7); out["rsi_14"] = rsi(out["close"], 14); out["rsi_21"] = rsi(out["close"], 21)
    out["macd"], out["macd_signal"], out["macd_hist"] = macd(out["close"])
    out["ema_9"] = ema(out["close"], 9); out["ema_12"] = ema(out["close"], 12)
    out["ema_26"] = ema(out["close"], 26); out["ema_50"] = ema(out["close"], 50)
    out["price_vs_ema9"]  = (out["close"] - out["ema_9"]) / (out["ema_9"] + 1e-12)
    out["price_vs_ema50"] = (out["close"] - out["ema_50"]) / (out["ema_50"] + 1e-12)
    out["atr_14"] = atr(out["high"], out["low"], out["close"], 14)
    out["atr_normalized"] = out["atr_14"] / (out["close"] + 1e-12)
    u, m, l = bollinger(out["close"], 20, 2.0)
    out["bb_upper"], out["bb_mid"], out["bb_lower"] = u, m, l
    out["bb_width"] = (u - l) / (m.replace(0, np.nan))
    out["bb_position"] = (out["close"] - l) / ((u - l) + 1e-12)
    # volume
    day_win = 5*78
    out["volume_sma"] = out["volume"].rolling(day_win, min_periods=78).mean()
    out["rel_volume"] = out["volume"] / (out["volume_sma"] + 1e-12)
    out["volume_momentum"] = out["volume"].pct_change(6)
    if "vwap" in out:
        out["price_vs_vwap"] = (out["close"] - out["vwap"]) / (out["vwap"] + 1e-12)
    # price action
    out["high_low_range"] = (out["high"] - out["low"]) / (out["close"] + 1e-12)
    out["body_size"] = (out["close"] - out["open"]).abs() / (out["close"] + 1e-12)
    out["upper_wick"] = (out["high"] - out[["open","close"]].max(axis=1)) / (out["close"] + 1e-12)
    out["lower_wick"] = (out[["open","close"]].min(axis=1) - out["low"]) / (out["close"] + 1e-12)
    out["gap_from_prev"] = (out["open"] - out["close"].shift(1)) / (out["close"].shift(1) + 1e-12)
    out["momentum_score"] = 0.2*out["return_5m"] + 0.3*out["return_30m"] + 0.5*out["return_1h"]
    return out

def add_stock_classification(df: pd.DataFrame, ticker: str) -> pd.DataFrame:
    info = STOCK_INFO.get(ticker, {'sector':'Unknown','industry':'Unknown','category':'Other','market_cap':'large','is_tech':0,'is_faang':0,'is_mag7':0})
    df["is_tech_stock"] = info['is_tech']; df["is_faang"] = info['is_faang']; df["is_mag7"] = info['is_mag7']
    df["market_cap_mega"] = 1 if info['market_cap']=='mega' else 0
    sec = info['sector']
    df["sector_technology"] = 1 if "Technology" in sec else 0
    df["sector_consumer"] = 1 if "Consumer" in sec else 0
    df["sector_healthcare"] = 1 if "Health" in sec else 0
    df["sector_financial"] = 1 if "Financial" in sec else 0
    return df

def add_etf_benchmarks(df_ticker: pd.DataFrame, etf_data: dict[str, pd.DataFrame]) -> pd.DataFrame:
    out = df_ticker.copy()
    for etf, edf in etf_data.items():
        if edf.empty: continue
        etf_close = edf["close"].reindex(out.index, method="ffill")
        out[f"{etf}_close"] = etf_close
        out[f"{etf}_ret_5m"]  = etf_close.pct_change()
        out[f"{etf}_ret_30m"] = etf_close.pct_change(6)
        out[f"{etf}_ret_1h"]  = etf_close.pct_change(12)
        out[f"vs_{etf}_5m"] = out["return_5m"] - out[f"{etf}_ret_5m"]
        out[f"vs_{etf}_1h"] = out["return_1h"] - out[f"{etf}_ret_1h"]
        cov = out["return_5m"].rolling(24, min_periods=12).cov(out[f"{etf}_ret_5m"])
        var = out[f"{etf}_ret_5m"].rolling(24, min_periods=12).var()
        out[f"beta_{etf}_2h"] = cov / (var + 1e-12)
        out[f"corr_{etf}_2h"] = out["return_5m"].rolling(24, min_periods=12).corr(out[f"{etf}_ret_5m"])
    if "SPY_ret_5m" in out and "QQQ_ret_5m" in out:
        out["risk_on_proxy"] = out["QQQ_ret_5m"] - out["SPY_ret_5m"]
        out["risk_on_cumsum_1h"] = out["risk_on_proxy"].rolling(12, min_periods=6).sum()
        if "SPY_ret_1h" in out and "QQQ_ret_1h" in out:
            out["tech_leadership"] = out["QQQ_ret_1h"] - out["SPY_ret_1h"]
    if "XLK_ret_5m" in out and "SPY_ret_5m" in out:
        out["tech_sector_rotation"] = out["XLK_ret_5m"] - out["SPY_ret_5m"]
    return out

def add_earnings_context(df: pd.DataFrame, ticker: str) -> pd.DataFrame:
    # META Q2 2024 after-close: 2024-07-31 (UTC marker ok)
    earnings = [pd.Timestamp("2024-07-31", tz="UTC")]
    df["days_to_earnings"] = 999.0; df["hours_to_earnings"] = 9999.0
    df["is_earnings_week"] = 0; df["is_earnings_day"] = 0
    df["is_pre_earnings"] = 0; df["is_post_earnings"] = 0
    for ed in earnings:
        dh = (ed - df.index).total_seconds() / 3600.0
        mask = np.abs(dh) < np.abs(df["hours_to_earnings"])
        df.loc[mask, "hours_to_earnings"] = dh[mask]
        df.loc[mask, "days_to_earnings"] = dh[mask] / 24.0
        df.loc[(df.index >= ed - pd.Timedelta(days=7)) & (df.index <= ed + pd.Timedelta(days=2)), "is_earnings_week"] = 1
        df.loc[(df.index >= ed - pd.Timedelta(hours=24)) & (df.index <= ed + pd.Timedelta(hours=24)), "is_earnings_day"] = 1
        df.loc[(df.index >= ed - pd.Timedelta(days=3)) & (df.index < ed), "is_pre_earnings"] = 1
        df.loc[(df.index > ed) & (df.index <= ed + pd.Timedelta(days=3)), "is_post_earnings"] = 1
    return df

def add_time_features(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    et = out.index.tz_convert("America/New_York")
    out["hour"] = et.hour; out["minute"] = et.minute; out["day_of_week"] = et.dayofweek
    out["is_premarket"] = (((et.hour >= 4) & (et.hour < 9)) | ((et.hour == 9) & (et.minute < 30))).astype(int)
    out["is_market_hours"] = (((et.hour > 9) | ((et.hour == 9) & (et.minute >= 30))) & (et.hour < 16)).astype(int)
    out["is_afterhours"] = ((et.hour >= 16) & (et.hour < 20)).astype(int)
    # 9:30–9:59 = opening 30m
    out["is_opening_30m"] = ((et.hour == 9) & (et.minute >= 30) & (et.minute < 60)).astype(int)
    out["is_power_hour"]  = (et.hour == 15).astype(int)
    out["is_close_15m"]   = ((et.hour == 15) & (et.minute >= 45)).astype(int)
    out["hour_sin"] = np.sin(2*np.pi*(et.hour + et.minute/60.0)/24.0)
    out["hour_cos"] = np.cos(2*np.pi*(et.hour + et.minute/60.0)/24.0)
    out["dow_sin"]  = np.sin(2*np.pi*et.dayofweek/5.0)
    out["dow_cos"]  = np.cos(2*np.pi*et.dayofweek/5.0)
    return out

def add_sentiment_placeholders(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    out["news_sentiment"]=0.0; out["news_count_1h"]=0
    out["twitter_sentiment"]=0.0; out["twitter_volume"]=0
    out["reddit_mentions"]=0; out["reddit_sentiment"]=0.0
    out["analyst_upgrades"]=0; out["analyst_downgrades"]=0
    out["insider_buy_signal"]=0; out["insider_sell_signal"]=0
    out["politician_trades"]=0
    out["options_put_call_ratio"]=np.nan
    return out

def add_labels(df: pd.DataFrame, threshold: float = 0.0005) -> pd.DataFrame:
    out = df.copy()
    out["target_5m_return"]  = out["close"].pct_change(-1)
    out["target_15m_return"] = out["close"].pct_change(-3)
    out["target_30m_return"] = out["close"].pct_change(-6)
    out["target_up_bin"] = (out["target_5m_return"] > threshold).astype(int)
    out["target_class"] = 0
    out.loc[out["target_5m_return"] >  0.002, "target_class"] = 2
    out.loc[(out["target_5m_return"] >  0.0005) & (out["target_5m_return"] <= 0.002), "target_class"] = 1
    out.loc[out["target_5m_return"] < -0.002, "target_class"] = -2
    out.loc[(out["target_5m_return"] >= -0.002) & (out["target_5m_return"] < -0.0005), "target_class"] = -1
    return out

def main():
    print(f"\n=== Enhanced Feature Builder for {TICKER} ({START} → {END}) ===\n")
    df = fetch_polygon_bars(TICKER, START, END, INTERVAL_MINUTES)
    if df.empty: print("❌ No data for primary ticker"); return
    print(f"✓ Primary bars: {len(df):,} ({df.index.min()} → {df.index.max()})")

    etfs = fetch_multiple_tickers(list(ETF_BENCHMARKS.keys()), START, END, INTERVAL_MINUTES)
    print(f"✓ ETF sets fetched: {len(etfs)} / {len(ETF_BENCHMARKS)}")

    feat = compute_core_features(df)
    feat = add_stock_classification(feat, TICKER)
    feat = add_etf_benchmarks(feat, etfs)
    feat = add_earnings_context(feat, TICKER)
    feat = add_time_features(feat)
    feat = add_sentiment_placeholders(feat)
    feat = add_labels(feat)

    # drop last bar (no future for label), then tidy columns/order
    feat = feat.iloc[:-1].copy().reset_index()

    preferred = [
        "timestamp","ticker","open","high","low","close","volume","vwap","trades",
        "is_tech_stock","is_faang","is_mag7","market_cap_mega",
        "sector_technology","sector_consumer","sector_healthcare","sector_financial",
        "return_5m","return_15m","return_30m","return_1h","return_4h",
        "volatility_30m","volatility_1h","volatility_4h",
        "rsi_7","rsi_14","rsi_21","macd","macd_signal","macd_hist",
        "ema_9","ema_12","ema_26","ema_50","price_vs_ema9","price_vs_ema50",
        "atr_14","atr_normalized","bb_upper","bb_mid","bb_lower","bb_width","bb_position",
        "volume_sma","rel_volume","volume_momentum",
        "high_low_range","body_size","upper_wick","lower_wick","gap_from_prev","momentum_score",
        "days_to_earnings","hours_to_earnings","is_earnings_week","is_earnings_day","is_pre_earnings","is_post_earnings",
        "hour","minute","day_of_week","is_premarket","is_market_hours","is_afterhours",
        "is_opening_30m","is_power_hour","is_close_15m","hour_sin","hour_cos","dow_sin","dow_cos",
        "news_sentiment","news_count_1h","twitter_sentiment","twitter_volume","reddit_mentions","reddit_sentiment",
        "analyst_upgrades","analyst_downgrades","insider_buy_signal","insider_sell_signal","politician_trades","options_put_call_ratio",
        "target_5m_return","target_15m_return","target_30m_return","target_up_bin","target_class"
    ]
    etf_syms = list(ETF_BENCHMARKS.keys())
    etf_dynamic = [c for c in feat.columns if any(sym in c for sym in etf_syms)]
    cols = [c for c in preferred if c in feat.columns]
    cols += [c for c in etf_dynamic if c not in cols]
    cols += [c for c in feat.columns if c not in cols]
    feat = feat[cols]

    feat.to_csv(OUT_CSV, index=False)
    print(f"\n✅ Wrote {len(feat):,} rows × {len(feat.columns)} cols → {OUT_CSV}")
    print(f"Target up (1): {(feat['target_up_bin']==1).sum():,}  ({(feat['target_up_bin']==1).mean()*100:.1f}%)")
    

if __name__ == "__main__":
    main()
