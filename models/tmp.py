import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import mean_squared_error, r2_score
import lightgbm as lgb
import matplotlib.pyplot as plt
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import LSTM, Dense, Dropout
from tensorflow.keras.optimizers import Adam
from tqdm import tqdm
from tensorflow.keras.callbacks import Callback
import sys

# === 1️⃣ データ読み込み ===
df = pd.read_csv("../data/colin_stock.csv")
df = df.sort_values("timestamp")

# === 2️⃣ 特徴量とターゲット ===
target = "target_15m_return"    # or 'target_up_bin' for classification
features = [c for c in df.columns if c not in ["timestamp", "ticker", target]]
X = df[features].fillna(0)
y = df[target]

# === 3️⃣ 学習・評価分割 ===
X_train, X_test, y_train, y_test = train_test_split(X, y, shuffle=False, test_size=0.2)

# === 4️⃣ LightGBM モデル ===

from tqdm import tqdm
import lightgbm as lgb

class TQDMCallback:
    """LightGBM 進捗表示用の tqdm コールバック"""
    def __init__(self, total_rounds):
        self.total_rounds = total_rounds
        self.pbar = tqdm(total=total_rounds, desc="Training LightGBM")

    def __call__(self, env):
        # LightGBM が呼び出す標準コールバック形式
        self.pbar.update(1)
        if env.evaluation_result_list:
            eval_name, eval_metric, val, _ = env.evaluation_result_list[0]
            self.pbar.set_postfix({eval_metric: f"{val:.6f}"})
        if env.iteration + 1 == self.total_rounds:
            self.pbar.close()

print("🚀 Training LightGBM...")
train_data = lgb.Dataset(X_train, label=y_train)
valid_data = lgb.Dataset(X_test, label=y_test)

params = {
    "objective": "regression",
    "metric": "mse",
    "learning_rate": 0.01,
    "num_leaves": 64,
    "max_depth": -1,
    "lambda_l2": 0.1,
    "feature_fraction": 0.8,
    "bagging_fraction": 0.8,
    "verbose": -1
}

n_rounds = 200
tqdm_cb = TQDMCallback(n_rounds)

lgbm_model = lgb.train(
    params,
    train_data,
    valid_sets=[valid_data],
    num_boost_round=n_rounds,
    callbacks=[tqdm_cb]
)

y_pred_lgb = lgbm_model.predict(X_test)
mse = mean_squared_error(y_test, y_pred_lgb)
r2 = r2_score(y_test, y_pred_lgb)
corr = np.corrcoef(y_test, y_pred_lgb)[0,1]
directional_acc = np.mean(np.sign(y_test) == np.sign(y_pred_lgb))

print(f"✅ LightGBM Metrics:")
print(f"  MSE: {mse:.6f}")
print(f"  R²: {r2:.3f}")
print(f"  Corr: {corr:.3f}")
print(f"  Directional Accuracy: {directional_acc:.3f}")

# === 5️⃣ tqdmでシーケンス作成の進捗可視化 ===
scaler = StandardScaler()
X_scaled = scaler.fit_transform(X)
window = 10  # lookback window

def create_seq(X, y, window):
    Xs, ys = [], []
    for i in tqdm(range(len(X) - window), desc="Creating LSTM sequences"):
        Xs.append(X[i:i+window])
        ys.append(y.iloc[i+window])
    return np.array(Xs), np.array(ys)

X_seq, y_seq = create_seq(X_scaled, y, window)
split = int(len(X_seq)*0.8)
X_train_seq, X_test_seq = X_seq[:split], X_seq[split:]
y_train_seq, y_test_seq = y_seq[:split], y_seq[split:]

# === 6️⃣ Keras学習にも進捗バー ===
class TQDMProgressBar(Callback):
    def on_train_begin(self, logs=None):
        self.epochs = self.params['epochs']
        self.progbar = tqdm(total=self.epochs, desc="Training LSTM", file=sys.stdout)

    def on_epoch_end(self, epoch, logs=None):
        self.progbar.update(1)
        self.progbar.set_postfix({
            "loss": f"{logs['loss']:.5f}",
            "val_loss": f"{logs['val_loss']:.5f}"
        })
    def on_train_end(self, logs=None):
        self.progbar.close()

model = Sequential([
    LSTM(64, return_sequences=True, input_shape=(window, X_seq.shape[2])),
    Dropout(0.2),
    LSTM(32),
    Dense(1)
])
model.compile(optimizer=Adam(0.001), loss="mse")

history = model.fit(
    X_train_seq, y_train_seq,
    validation_data=(X_test_seq, y_test_seq),
    epochs=30,
    batch_size=32,
    verbose=0,
    callbacks=[TQDMProgressBar()]
)

# === 7️⃣ 評価 ===
y_pred_lstm = model.predict(X_test_seq).flatten()
mse_lstm = mean_squared_error(y_test_seq, y_pred_lstm)
r2_lstm = r2_score(y_test_seq, y_pred_lstm)
corr_lstm = np.corrcoef(y_test_seq, y_pred_lstm)[0,1]
dir_acc_lstm = np.mean(np.sign(y_test_seq) == np.sign(y_pred_lstm))

print(f"\n✅ LSTM Metrics:")
print(f"  MSE: {mse_lstm:.6f}")
print(f"  R²: {r2_lstm:.3f}")
print(f"  Corr: {corr_lstm:.3f}")
print(f"  Directional Accuracy: {dir_acc_lstm:.3f}")

# === 8️⃣ シミュレーション ===
df_test = df.iloc[-len(y_test):].copy()
df_test["pred"] = y_pred_lgb
df_test["signal"] = np.sign(df_test["pred"])
df_test["profit"] = df_test["signal"] * df_test[target]
df_test["cum_profit"] = df_test["profit"].cumsum()

plt.figure(figsize=(8,4))
plt.plot(df_test["timestamp"], df_test["cum_profit"], label="Simulated Cumulative Profit")
plt.xlabel("Time")
plt.ylabel("Cumulative Return")
plt.legend()
plt.show()

total_profit = df_test["cum_profit"].iloc[-1]
print(f"💰 Total simulated profit: {total_profit:.4f}")
