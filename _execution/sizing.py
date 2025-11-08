# python/valuecell_trader/execution/sizing.py
"""
Position sizing logic
"""
from typing import Dict, Optional
from ..storage.schemas import Allocation
from ..config.schema import RiskConfig


class PositionSizer:
    """Calculate position sizes using Kelly criterion"""

    def __init__(self, risk_config: RiskConfig):
        self.config = risk_config

    def size_position(
        self,
        ticker: str,
        s_final: float,
        capital: float,
        current_exposures: Dict[str, float],
        sector_exposures: Dict[str, float] = None,
    ) -> Optional[Allocation]:
        """
        Calculate position size

        Args:
            ticker: Ticker symbol
            s_final: Final investment score [0, 1]
            capital: Available capital
            current_exposures: Dict of ticker -> exposure
            sector_exposures: Dict of sector -> exposure

        Returns:
            Allocation object or None if should not enter
        """
        # Check if meets entry threshold
        if s_final < 0.5:  # Below neutral
            return None

        # Calculate Kelly-lite fraction
        # f* = k * (2*S_final - 1)+
        kelly_fraction = self.config.kelly_scale * max(0, 2 * s_final - 1)

        if kelly_fraction <= 0:
            return None

        # Calculate target notional
        target_notional = kelly_fraction * capital

        # Apply per-name cap
        max_per_name = self.config.max_per_name * capital
        target_notional = min(target_notional, max_per_name)

        # Check total exposure cap
        total_exposure = sum(current_exposures.values())
        available_exposure = self.config.max_total_exposure * capital - total_exposure

        if available_exposure <= 0:
            return Allocation(
                ticker=ticker,
                target_notional=0,
                target_quantity=0,
                s_final=s_final,
                reason="max_total_exposure_reached",
            )

        target_notional = min(target_notional, available_exposure)

        # Apply sector cap if provided
        if sector_exposures:
            # Simplified: would need sector mapping in production
            pass

        return Allocation(
            ticker=ticker,
            target_notional=target_notional,
            target_quantity=0,  # Will be calculated by order manager
            s_final=s_final,
            reason="normal_entry",
        )
