# python/valuecell_trader/features/market_features.py
"""
Market feature extraction from price data
"""
from typing import List, Dict, Any
import numpy as np
import pandas as pd

from ..storage.schemas import PriceBar


class MarketFeatureBuilder:
    """Build features from market data"""

    def build_features(
            self,
            ticker: str,
            bars: List[PriceBar],
            current_bar: PriceBar
    ) -> Dict[str, Any]:
        """
        Build market features from price bars

        Args:
            ticker: Ticker symbol
            bars: Historical price bars
            current_bar: Current price bar

        Returns:
            Dictionary of features
        """
        if len(bars) < 30:
            return self._get_default_features()

        # Convert to DataFrame for easier calculation
        df = pd.DataFrame([
            {
                'close': b.close,
                'high': b.high,
                'low': b.low,
                'volume': b.volume
            }
            for b in bars
        ])

        # Calculate return z-score
        returns = df['close'].pct_change()
        mean_return = returns.tail(20).mean()
        std_return = returns.tail(20).std()
        current_return = (current_bar.close - bars[-2].close) / bars[-2].close if len(bars) >= 2 else 0
        return_zscore = (current_return - mean_return) / std_return if std_return > 0 else 0

        # Calculate RSI(14)
        rsi = self._calculate_rsi(df['close'].values, period=14)

        # Calculate ATR(14)
        atr = self._calculate_atr(df['high'].values, df['low'].values, df['close'].values, period=14)

        # Calculate volume ratio
        avg_volume_30d = df['volume'].tail(30).mean()
        volume_ratio = current_bar.volume / avg_volume_30d if avg_volume_30d > 0 else 1.0

        return {
            'return_zscore': return_zscore,
            'rsi': rsi,
            'atr': atr,
            'volume_ratio': volume_ratio,
            'spread_bps': current_bar.spread_bps or 5.0
        }

    def _calculate_rsi(self, prices: np.ndarray, period: int = 14) -> float:
        """Calculate Relative Strength Index"""
        if len(prices) < period + 1:
            return 50.0

        deltas = np.diff(prices)
        gains = np.where(deltas > 0, deltas, 0)
        losses = np.where(deltas < 0, -deltas, 0)

        avg_gain = np.mean(gains[-period:])
        avg_loss = np.mean(losses[-period:])

        if avg_loss == 0:
            return 100.0

        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))

        return rsi

    def _calculate_atr(self, highs: np.ndarray, lows: np.ndarray, closes: np.ndarray, period: int = 14) -> float:
        """Calculate Average True Range"""
        if len(highs) < period + 1:
            return 0.0

        tr_list = []
        for i in range(1, len(highs)):
            hl = highs[i] - lows[i]
            hc = abs(highs[i] - closes[i - 1])
            lc = abs(lows[i] - closes[i - 1])
            tr = max(hl, hc, lc)
            tr_list.append(tr)

        atr = np.mean(tr_list[-period:])
        return atr

    def _get_default_features(self) -> Dict[str, Any]:
        """Return default features when insufficient data"""
        return {
            'return_zscore': 0.0,
            'rsi': 50.0,
            'atr': 0.0,
            'volume_ratio': 1.0,
            'spread_bps': 5.0
        }