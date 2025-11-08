# python/valuecell_trader/execution/risk.py
"""
Risk management logic
"""
from typing import Dict, Optional
from datetime import datetime, timedelta
from ..storage.schemas import Position, PriceBar
from ..config.schema import RiskConfig


class RiskManager:
    """Manage position risk and exits"""

    def __init__(self, risk_config: RiskConfig):
        self.config = risk_config

    def calculate_stops(self, entry_price: float, atr: Optional[float] = None) -> tuple:
        """
        Calculate stop loss and take profit levels

        Args:
            entry_price: Entry price
            atr: Average True Range (optional for ATR-based stops)

        Returns:
            (stop_price, tp_price)
        """
        # Hard stop
        stop_price = entry_price * (1 - self.config.stop_pct)

        # ATR-based stop if available
        if atr:
            atr_stop = entry_price - 1.2 * atr
            stop_price = max(stop_price, atr_stop)

        # Take profit
        tp_price = entry_price * (1 + self.config.tp_pct)

        return stop_price, tp_price

    def check_exits(
        self,
        position: Position,
        current_bar: PriceBar,
        current_time: datetime,
        p_drop: float,
    ) -> Optional[str]:
        """
        Check if position should be exited

        Args:
            position: Current position
            current_bar: Current price bar
            current_time: Current timestamp
            p_drop: Current knee-jerk probability

        Returns:
            Exit reason or None if should hold
        """
        current_price = current_bar.close

        # Check stop loss
        if current_price <= position.stop_price:
            return "stop_loss"

        # Check take profit
        if current_price >= position.tp_price:
            return "take_profit"

        # Check timeout
        if current_time >= position.timeout_time:
            return "timeout"

        # Check knee-jerk exit
        if p_drop > self.config.scoring.kneejerk_cut:
            return "kneejerk"

        return None
