# stock_updown_train_eval.py
import pandas as pd
import numpy as np
from sklearn.experimental import enable_hist_gradient_boosting  # noqa: F401
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.metrics import (
    accuracy_score, roc_auc_score, f1_score, confusion_matrix, classification_report
)
from sklearn.model_selection import train_test_split

# ==== 設定 ====
CSV_PATH   = "../data/colin_stock.csv"      # ←ここを書き換え
SYMBOL     = "META" # 例: "META" に絞るなら "META"、全部使うなら None
TARGET_COL = "target_up_bin"                   # 既存の2値ラベル（上=1, 下=0 想定）
EVAL_START = "2024-04-05 20:15:00+00:00"       # 時系列Splitの境界（UTC）

# ==== 1) 読み込み ====
df = pd.read_csv(CSV_PATH)
# 時刻
ts_col = [c for c in df.columns if c.lower().startswith("timestamp")][0]
df[ts_col] = pd.to_datetime(df[ts_col])

# 銘柄フィルタ
if SYMBOL is not None and "ticker" in df.columns:
    df = df[df["ticker"] == SYMBOL].copy()

# ラベル存在チェック
if TARGET_COL not in df.columns:
    raise ValueError(f"{TARGET_COL} が見つかりません。CSV内のラベル列名を確認してください。")

# ==== 2) リークしそうな列を除外 ====
drop_exact = {
    ts_col, "ticker",
    # 未来のリターン/ラベル（CSVにあるものは全部除外）
    "target_5m_return", "target_15m_return", "target_30m_return",
    "target_class", "target_up_bin",
}
# テキトーに “見た瞬間に未来が分かりそう” な列名をフィルタ（必要に応じて調整）
leak_keywords = [
    "target_",        # 未来リターン系
    "hours_to_earnings","days_to_earnings",  # 将来イベントまでの残時間（生成方法によっては未来参照）
]
feature_cols = []
for c in df.columns:
    if c in drop_exact: 
        continue
    if any(k in c for k in leak_keywords):
        continue
    feature_cols.append(c)

# 欠損処理（HGBC は NaN を扱えるが、極端に欠損が多い列を落としておくと安定）
Xfull = df[feature_cols].copy()
too_nan = Xfull.isna().mean() > 0.25   # 25%超欠損列はドロップ
keep_cols = list(too_nan[~too_nan].index)
Xfull = Xfull[keep_cols]
Xfull = Xfull.fillna(Xfull.median(numeric_only=True))

yfull = df[TARGET_COL].astype(int)

# ==== 3) 時系列スプリット ====
eval_start_ts = pd.to_datetime(EVAL_START)
train_mask = df[ts_col] < eval_start_ts
eval_mask  = df[ts_col] >= eval_start_ts

X_train, y_train = Xfull[train_mask], yfull[train_mask]
X_eval,  y_eval  = Xfull[eval_mask],  yfull[eval_mask]
ts_eval         = df.loc[eval_mask, ts_col].reset_index(drop=True)

if len(X_train) == 0 or len(X_eval) == 0:
    raise ValueError("train/eval のどちらかが空です。EVAL_START を調整してください。")

# ==== 4) 学習 ====
clf = HistGradientBoostingClassifier(
    max_depth=None,
    learning_rate=0.06,
    max_iter=120,
    min_samples_leaf=20,
    l2_regularization=0.0,
    random_state=42
)
clf.fit(X_train, y_train)

# ==== 5) 推論 & 評価 ====
proba = clf.predict_proba(X_eval)[:, 1]
pred  = (proba >= 0.5).astype(int)

acc  = accuracy_score(y_eval, pred)
auc  = roc_auc_score(y_eval, proba) if len(np.unique(y_eval)) > 1 else np.nan
f1   = f1_score(y_eval, pred)
cm   = confusion_matrix(y_eval, pred)
dir_acc = acc  # 上下2値の “方向一致率” はここでは Accuracy と同義

print("=== Eval Metrics ===")
print(f"Samples (train/eval): {len(X_train)} / {len(X_eval)}")
print(f"Accuracy : {acc:.3f}")
print(f"ROC-AUC  : {auc:.3f}")
print(f"F1-score : {f1:.3f}")
print("Confusion Matrix [y=0,1 rows]:\n", cm)
print("\nClassification report:\n", classification_report(y_eval, pred, digits=3))

# ==== 6) 予測を書き出し ====
out = pd.DataFrame({
    "timestamp": ts_eval,
    "pred_up": pred,
    "proba_up": proba,
    "y_true": y_eval.reset_index(drop=True),
})
out.to_csv("eval_preds.csv", index=False)
print("\nSaved: eval_preds.csv")

# ==== 7) ざっくりFeature Importance（平均|shap値じゃないが目安） ====
# HistGB はネイティブの importance を持たないので、単純Permutation ImportanceでもOK
try:
    from sklearn.inspection import permutation_importance
    r = permutation_importance(clf, X_eval, y_eval, n_repeats=5, random_state=42)
    imp = (
        pd.DataFrame({"feature": X_eval.columns, "importance": r.importances_mean})
        .sort_values("importance", ascending=False)
        .head(25)
    )
    print("\nTop features:\n", imp)
    imp.to_csv("feature_importance_top25.csv", index=False)
    print("Saved: feature_importance_top25.csv")
except Exception as e:
    print("Permutation importance skipped:", e)
