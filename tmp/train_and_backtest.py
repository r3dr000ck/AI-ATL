#!/usr/bin/env python3
"""
train_and_backtest.py
---------------------
Merge price features (colin_stock.csv) + news embeddings, train a classifier, and backtest with $1000 initial capital.

Example:
  python train_and_backtest.py \
    --price_csv colin_stock.csv \
    --emb_csv meta_emb.csv \
    --ticker META \
    --p_up 0.60 \
    --fee_bps 2 \
    --slip_bps 1 \
    --out_prefix meta_run

Outputs:
  - <out_prefix>_metrics.txt
  - <out_prefix>_equity.csv
  - <out_prefix>_feature_importance.csv (if LightGBM)
  - shows equity plot
"""

import argparse, sys, os
import pandas as pd, numpy as np
import matplotlib.pyplot as plt

def load_embeddings_csv(path):
    emb = pd.read_csv(path)
    emb["date"] = pd.to_datetime(emb["date"], utc=True, errors="coerce")
    emb["ts5"] = emb["date"].dt.floor("5min")
    emb_cols = [c for c in emb.columns if c.startswith("emb_")]
    emb_agg = emb.groupby("ts5")[emb_cols].mean().reset_index()
    return emb_agg, emb_cols

def prepare_price_df(price_csv, ticker):
    df = pd.read_csv(price_csv)
    df["timestamp"] = pd.to_datetime(df["timestamp"], utc=True)
    if "ticker" in df.columns:
        df = df[df["ticker"]==ticker].copy()
    df["ts5"] = df["timestamp"].dt.floor("5min")
    return df

def main():
    ap = argparse.ArgumentParser(description="Train model on price+embeddings and backtest.")
    ap.add_argument("--price_csv", required=True)
    ap.add_argument("--emb_csv", required=True)
    ap.add_argument("--ticker", required=True)
    ap.add_argument("--p_up", type=float, default=0.60, help="Prob threshold to go long")
    ap.add_argument("--fee_bps", type=float, default=2, help="fee per side in bps")
    ap.add_argument("--slip_bps", type=float, default=1, help="slippage per trade in bps")
    ap.add_argument("--capital", type=float, default=1000.0)
    ap.add_argument("--out_prefix", default="run")
    args = ap.parse_args()

    emb_agg, emb_cols = load_embeddings_csv(args.emb_csv)
    price_df = prepare_price_df(args.price_csv, args.ticker)
    merged = price_df.merge(emb_agg, on="ts5", how="left")
    for c in [col for col in merged.columns if col.startswith("emb_")]:
        merged[c] = merged[c].fillna(0.0)

    # Target: future up/down (15m ahead if present, else 1-step)
    if "future_close" not in merged.columns:
        merged["future_close"] = merged["close"].shift(-3)  # ~15m ahead for 5m bars
    y = (merged["future_close"] > merged["close"]).astype(int).values
    merged = merged.dropna(subset=["future_close"]).copy()

    # Features: price tech + embeddings
    tech_cols = [
        "return_5m","return_15m","return_30m","price_vs_vwap","rsi_7",
        "macd","macd_signal","macd_hist","ema_9","ema_12","ema_26","ema_50",
        "atr_normalized","bb_width","bb_position"
    ]
    tech_cols = [c for c in tech_cols if c in merged.columns]
    X = merged[tech_cols + [c for c in merged.columns if c.startswith("emb_")]].fillna(0.0)

    # Chrono split
    split = int(0.8*len(X))
    X_train, X_test = X.iloc[:split], X.iloc[split:]
    y_train, y_test = y[:split], y[split:]

    model_name = None
    fi_df = None
    proba = None
    try:
        import lightgbm as lgb
        model = lgb.LGBMClassifier(
            objective="binary",
            metric="auc",
            learning_rate=0.03,
            num_leaves=63,
            feature_fraction=0.8,
            bagging_fraction=0.9,
            bagging_freq=5,
            reg_lambda=2.0,
            n_estimators=800,
            random_state=42
        )
        model.fit(X_train, y_train)
        proba = model.predict_proba(X_test)[:,1]
        model_name = "LightGBM"
        try:
            fi_df = pd.DataFrame({"feature": X.columns, "importance": model.booster_.feature_importance()})
        except Exception:
            pass
    except Exception:
        # fallback
        from sklearn.linear_model import LogisticRegression
        from sklearn.preprocessing import StandardScaler
        from sklearn.pipeline import Pipeline
        model = Pipeline([("scaler", StandardScaler(with_mean=False)), ("clf", LogisticRegression(max_iter=400))])
        model.fit(X_train, y_train)
        from sklearn.preprocessing import minmax_scale
        try:
            proba = model.predict_proba(X_test)[:,1]
        except Exception:
            proba = minmax_scale(model.decision_function(X_test))
        model_name = "LogReg"

    import numpy as np
    pred = (proba >= args.p_up).astype(int)

    # Backtest on test slice
    test_slice = merged.iloc[split:].copy()
    fee = args.fee_bps/10000.0
    slip = args.slip_bps/10000.0

    capital = args.capital
    cash = capital
    pos = 0.0  # number of shares
    equity = []

    for i, row in test_slice.iterrows():
        price = float(row["close"])
        signal = int(pred[i - split])
        # Desired position: long when signal=1, else flat
        desired_pos = int(cash // (price*(1+fee+slip))) if signal==1 else 0

        # Adjust position if needed
        if desired_pos > pos:
            # buy difference
            buy_shares = desired_pos - pos
            cash -= buy_shares * price * (1+fee+slip)
            pos += buy_shares
        elif desired_pos < pos:
            sell_shares = pos - desired_pos
            cash += sell_shares * price * (1-fee-slip)
            pos -= sell_shares

        equity.append(cash + pos*price)

    equity = pd.Series(equity, index=test_slice["timestamp"].values)
    out_equity = pd.DataFrame({"timestamp": test_slice["timestamp"].values, "equity": equity.values})
    out_equity.to_csv(f"{args.out_prefix}_equity.csv", index=False)

    # Metrics
    final_value = equity.iloc[-1] if len(equity)>0 else capital
    total_return = (final_value / capital - 1.0) if capital>0 else 0.0

    with open(f"{args.out_prefix}_metrics.txt", "w") as f:
        f.write(f"Model={model_name}\n")
        f.write(f"Capital=${capital:,.2f}\n")
        f.write(f"Final=${final_value:,.2f}\n")
        f.write(f"Return={total_return*100:.2f}%\n")
        f.write(f"p_up={args.p_up}, fee_bps={args.fee_bps}, slip_bps={args.slip_bps}\n")

    if fi_df is not None:
        fi_df.sort_values("importance", ascending=False).to_csv(f"{args.out_prefix}_feature_importance.csv", index=False)

    # Plot
    plt.figure(figsize=(9,5))
    plt.plot(out_equity["timestamp"], out_equity["equity"], label="Equity", lw=2)
    plt.title(f"{args.ticker} — {model_name} — ${capital:,.0f} starting capital")
    plt.xlabel("Time"); plt.ylabel("Equity ($)"); plt.grid(True); plt.legend(); plt.tight_layout()
    plt.savefig(f"{args.out_prefix}_equity.png", dpi=140)
    try:
        plt.show()
    except Exception:
        pass

    print(f"Wrote: {args.out_prefix}_metrics.txt, {args.out_prefix}_equity.csv, {args.out_prefix}_equity.png")
    if fi_df is not None:
        print(f"Wrote: {args.out_prefix}_feature_importance.csv")

if __name__ == "__main__":
    main()
