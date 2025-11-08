# python/valuecell_trader/models/model_trainer.py
"""
Model training utilities
"""
import numpy as np
import pandas as pd
from typing import Dict, Any, List, Tuple, Optional
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.metrics import classification_report, confusion_matrix
import logging

from .__init__ import PUpModel
from .p_drop import PDropModel
from .r_vol import RVolModel
from .calibration import calculate_brier_score, calculate_reliability_curve

logger = logging.getLogger(__name__)


class ModelTrainer:
    """
    Train and evaluate trading models
    """

    def __init__(self):
        self.p_up_model = PUpModel()
        self.p_drop_model = PDropModel()
        self.r_vol_model = RVolModel()

    def prepare_training_data(
        self, historical_features: pd.DataFrame, historical_outcomes: pd.DataFrame
    ) -> Tuple[np.ndarray, Dict[str, np.ndarray]]:
        """
        Prepare training data from historical backtests

        Args:
            historical_features: DataFrame with feature vectors
            historical_outcomes: DataFrame with outcome labels

        Returns:
            (X, y_dict) where y_dict contains labels for each model
        """
        # Align features and outcomes
        aligned = pd.merge(
            historical_features,
            historical_outcomes,
            on=["ticker", "timestamp"],
            how="inner",
        )

        # Extract feature matrix
        feature_cols = [
            "sentiment_weighted",
            "event_count_1h",
            "sentiment_delta",
            "return_zscore",
            "rsi",
            "atr",
            "volume_ratio",
            "spread_bps",
        ]

        X = aligned[feature_cols].values

        # Extract labels for each model
        y_dict = {
            "p_up": (aligned["return_1d"] > 0).astype(int).values,
            "p_drop": (aligned["return_1d"] < -0.02).astype(int).values,
            "r_vol": (aligned["volatility_spike"] == 1).astype(int).values,
        }

        return X, y_dict

    def train_all_models(
        self, X: np.ndarray, y_dict: Dict[str, np.ndarray], test_size: float = 0.2
    ) -> Dict[str, Any]:
        """
        Train all models and return evaluation metrics

        Args:
            X: Feature matrix
            y_dict: Labels for each model
            test_size: Proportion of data for testing

        Returns:
            Dictionary with training results
        """
        results = {}

        # Split data
        X_train, X_test, y_train_up, y_test_up = train_test_split(
            X, y_dict["p_up"], test_size=test_size, random_state=42
        )

        _, _, y_train_drop, y_test_drop = train_test_split(
            X, y_dict["p_drop"], test_size=test_size, random_state=42
        )

        _, _, y_train_vol, y_test_vol = train_test_split(
            X, y_dict["r_vol"], test_size=test_size, random_state=42
        )

        # Train P_up model
        logger.info("Training P_up model...")
        self.p_up_model.train(X_train, y_train_up)

        # Evaluate P_up
        y_pred_up = np.array(
            [
                self.p_up_model.predict(self._array_to_features(X_test[i]))
                for i in range(len(X_test))
            ]
        )

        results["p_up"] = {
            "brier_score": calculate_brier_score(y_test_up, y_pred_up),
            "accuracy": np.mean((y_pred_up > 0.5) == y_test_up),
            "reliability": calculate_reliability_curve(y_test_up, y_pred_up),
        }

        logger.info(f"P_up Brier score: {results['p_up']['brier_score']:.4f}")
        logger.info(f"P_up Accuracy: {results['p_up']['accuracy']:.4f}")

        # Train R_vol model
        logger.info("Training R_vol model...")
        self.r_vol_model.train(X_train, y_train_vol)

        # Evaluate R_vol
        y_pred_vol = np.array(
            [
                self.r_vol_model.predict(self._array_to_features(X_test[i]))
                for i in range(len(X_test))
            ]
        )

        results["r_vol"] = {
            "brier_score": calculate_brier_score(y_test_vol, y_pred_vol),
            "accuracy": np.mean((y_pred_vol > 0.5) == y_test_vol),
        }

        logger.info(f"R_vol Brier score: {results['r_vol']['brier_score']:.4f}")

        return results

    def _array_to_features(self, arr: np.ndarray) -> Dict[str, Any]:
        """Convert feature array back to dictionary"""
        return {
            "sentiment_weighted": arr[0],
            "event_count_1h": arr[1],
            "sentiment_delta": arr[2],
            "return_zscore": arr[3],
            "rsi": arr[4],
            "atr": arr[5],
            "volume_ratio": arr[6],
            "spread_bps": arr[7],
        }

    def save_models(self, base_path: str):
        """Save all trained models"""
        self.p_up_model.save(f"{base_path}/p_up_model.pkl")
        self.r_vol_model.save(f"{base_path}/r_vol_model.pkl")
        logger.info(f"Models saved to {base_path}")

    def load_models(self, base_path: str):
        """Load trained models"""
        self.p_up_model.load(f"{base_path}/p_up_model.pkl")
        self.r_vol_model.load(f"{base_path}/r_vol_model.pkl")
        logger.info(f"Models loaded from {base_path}")
