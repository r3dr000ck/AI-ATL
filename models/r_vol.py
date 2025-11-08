# python/valuecell_trader/models/r_vol.py
"""
R_vol (Volatility Spike) model
Predicts probability of volatility spike
"""
import numpy as np
from typing import Dict, Any
from sklearn.ensemble import RandomForestClassifier
import pickle


class RVolModel:
    """
    Volatility spike prediction model
    Predicts probability of significant volatility increase
    """

    def __init__(self):
        self.model = None
        self.is_trained = False
        self.threshold_multiplier = 1.5  # Define "spike" as 1.5x normal vol

    def predict(self, features: Dict[str, Any]) -> float:
        """
        Predict probability of volatility spike

        Args:
            features: Feature dictionary

        Returns:
            Probability in [0, 1]
        """
        if not self.is_trained:
            return self._heuristic_predict(features)

        # Use trained model
        X = self._features_to_array(features)
        prob = self.model.predict_proba(X)[0, 1]
        return float(prob)

    def _heuristic_predict(self, features: Dict[str, Any]) -> float:
        """
        Heuristic volatility spike prediction

        Factors:
        - Event count spikes
        - Sentiment volatility (large swings)
        - Volume spikes
        - Market stress indicators
        """
        prob = 0.1  # Base probability

        # Event count spike
        event_count = features.get("event_count_1h", 0)
        if event_count >= 5:
            prob += 0.3
        elif event_count >= 3:
            prob += 0.2

        # Sentiment volatility (large absolute values or deltas)
        sentiment = abs(features.get("sentiment_weighted", 0))
        sentiment_delta = abs(features.get("sentiment_delta", 0))

        if sentiment > 0.5:
            prob += 0.2
        if sentiment_delta > 0.3:
            prob += 0.15

        # Volume spike
        volume_ratio = features.get("volume_ratio", 1.0)
        if volume_ratio > 3.0:
            prob += 0.25
        elif volume_ratio > 2.0:
            prob += 0.15

        # Market extension (often precedes volatility)
        rsi = features.get("rsi", 50)
        if rsi > 75 or rsi < 25:
            prob += 0.15

        # Return z-score extremes
        z_score = abs(features.get("return_zscore", 0))
        if z_score > 2.0:
            prob += 0.2
        elif z_score > 1.5:
            prob += 0.1

        # Event tags
        event_tags = features.get("event_tags", {})
        if event_tags.get("earnings", 0) > 0:
            prob += 0.2  # Earnings often increase volatility
        if event_tags.get("mna", 0) > 0:
            prob += 0.25  # M&A creates volatility
        if event_tags.get("lawsuit", 0) > 0:
            prob += 0.15

        # Clamp to [0, 1]
        return max(0.0, min(1.0, prob))

    def train(self, X_train: np.ndarray, y_train: np.ndarray):
        """
        Train volatility spike model

        Args:
            X_train: Training features
            y_train: Training labels (1 = volatility spike, 0 = normal)
        """
        self.model = RandomForestClassifier(
            n_estimators=100, max_depth=10, random_state=42
        )
        self.model.fit(X_train, y_train)
        self.is_trained = True

    def _features_to_array(self, features: Dict[str, Any]) -> np.ndarray:
        """Convert feature dict to numpy array"""
        feature_list = [
            features.get("sentiment_weighted", 0),
            features.get("event_count_1h", 0),
            features.get("sentiment_delta", 0),
            features.get("return_zscore", 0),
            features.get("rsi", 50),
            features.get("atr", 0),
            features.get("volume_ratio", 1),
            features.get("spread_bps", 5),
            abs(features.get("sentiment_weighted", 0)),
            abs(features.get("sentiment_delta", 0)),
            abs(features.get("return_zscore", 0)),
        ]
        return np.array(feature_list).reshape(1, -1)

    def save(self, path: str):
        """Save model to disk"""
        with open(path, "wb") as f:
            pickle.dump({"model": self.model, "is_trained": self.is_trained}, f)

    def load(self, path: str):
        """Load model from disk"""
        with open(path, "rb") as f:
            data = pickle.load(f)
            self.model = data["model"]
            self.is_trained = data["is_trained"]
