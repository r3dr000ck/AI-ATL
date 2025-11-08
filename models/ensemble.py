# python/valuecell_trader/models/ensemble.py
"""
Ensemble scorer - Combines all model outputs into final decision
"""
import numpy as np
from typing import Dict, Any, Optional
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class EnsembleScorer:
    """
    Ensemble model that combines P_up, D_ext, P_drop, and R_vol
    into a final investment score and action recommendation
    """

    def __init__(self, beta: float = 0.3):
        """
        Args:
            beta: EMA smoothing parameter for temporal stability
        """
        self.beta = beta
        self.prev_scores: Dict[str, float] = {}

    def calculate_final_score(
        self,
        p_up: float,
        d_ext: float,
        p_drop: float,
        r_vol: Optional[float] = None,
        ticker: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Calculate final investment score and recommendation

        Args:
            p_up: Upward probability [0, 1]
            d_ext: Extension dampener [0, 1]
            p_drop: Downside probability [0, 1]
            r_vol: Volatility spike probability [0, 1] (optional)
            ticker: Ticker symbol for EMA tracking

        Returns:
            Dictionary with final score, expected move, and action
        """
        # Raw score calculation
        # S_raw = P_up × D_ext × (1 - P_drop)
        s_raw = p_up * d_ext * (1 - p_drop)

        # Apply volatility adjustment if available
        if r_vol is not None:
            # Reduce score if high volatility expected
            # High vol = uncertainty = reduce conviction
            vol_dampener = 1 - (r_vol * 0.3)  # Max 30% reduction
            s_raw *= vol_dampener

        # Apply EMA smoothing for stability
        if ticker and ticker in self.prev_scores:
            s_final = (1 - self.beta) * self.prev_scores[ticker] + self.beta * s_raw
        else:
            s_final = s_raw

        # Store for next iteration
        if ticker:
            self.prev_scores[ticker] = s_final

        # Calculate expected move magnitude
        # Combination of conviction and volatility
        expected_move = self._calculate_expected_move(p_up, p_drop, r_vol, d_ext)

        # Determine action
        action = self._determine_action(s_final, p_drop, r_vol)

        # Calculate confidence
        confidence = self._calculate_confidence(p_up, p_drop, d_ext, r_vol)

        return {
            "s_final": float(s_final),
            "s_raw": float(s_raw),
            "expected_move": expected_move,
            "action": action,
            "confidence": confidence,
            "components": {
                "p_up": p_up,
                "d_ext": d_ext,
                "p_drop": p_drop,
                "r_vol": r_vol,
            },
        }

    def _calculate_expected_move(
        self, p_up: float, p_drop: float, r_vol: Optional[float], d_ext: float
    ) -> Optional[float]:
        """
        Calculate expected percentage move

        Combines directional probabilities with volatility
        """
        if r_vol is None:
            r_vol = 0.3  # Default moderate volatility

        # Base move expectation
        # Positive if p_up > p_drop, negative otherwise
        directional_edge = p_up - p_drop

        # Scale by volatility
        # High vol = larger expected moves
        base_vol = 0.02  # 2% base daily move
        vol_multiplier = 1 + (r_vol * 2)  # Up to 3x for high vol

        expected_move = directional_edge * base_vol * vol_multiplier

        # Dampen if extended
        expected_move *= d_ext

        return float(expected_move)

    def _determine_action(
        self, s_final: float, p_drop: float, r_vol: Optional[float]
    ) -> str:
        """
        Determine recommended action

        Returns: 'BUY', 'SELL', or 'HOLD'
        """
        # Knee-jerk exit override
        if p_drop > 0.6:
            return "SELL"

        # High volatility = more conservative thresholds
        vol_adjustment = 0.0
        if r_vol and r_vol > 0.6:
            vol_adjustment = 0.05  # Require higher conviction in high vol

        buy_threshold = 0.60 + vol_adjustment
        sell_threshold = 0.40 - vol_adjustment

        if s_final >= buy_threshold:
            return "BUY"
        elif s_final <= sell_threshold:
            return "SELL"
        else:
            return "HOLD"

    def _calculate_confidence(
        self, p_up: float, p_drop: float, d_ext: float, r_vol: Optional[float]
    ) -> float:
        """
        Calculate confidence in the recommendation

        Higher confidence when:
        - Clear directional edge (p_up or p_drop high)
        - Low extension (d_ext near 1)
        - Low volatility uncertainty
        """
        # Directional confidence
        directional_conf = max(p_up, p_drop)

        # Extension confidence (more confident when not extended)
        extension_conf = d_ext

        # Volatility confidence (more confident with low vol)
        if r_vol is not None:
            vol_conf = 1 - r_vol
        else:
            vol_conf = 0.7  # Default moderate confidence

        # Weighted combination
        confidence = 0.5 * directional_conf + 0.25 * extension_conf + 0.25 * vol_conf

        return float(confidence)

    def reset_ema(self, ticker: Optional[str] = None):
        """
        Reset EMA tracking

        Args:
            ticker: If provided, reset only this ticker. Otherwise reset all.
        """
        if ticker:
            self.prev_scores.pop(ticker, None)
        else:
            self.prev_scores.clear()
