# python/valuecell_trader/execution/broker_paper.py
"""
Paper trading broker adapter
"""
from typing import List, Dict, Optional
from datetime import datetime
import uuid

from ..storage.schemas import Order, ExecutionReport, Position, PriceBar


class PaperBroker:
    """Paper trading broker implementation"""

    def __init__(self, initial_capital: float = 1000.0):
        self.capital = initial_capital
        self.positions: Dict[str, Position] = {}
        self.orders: Dict[str, Order] = {}
        self.execution_history: List[ExecutionReport] = []

    def submit_order(
        self,
        order: Order,
        current_bar: PriceBar,
        slippage_bps: float = 10,
        fee_bps: float = 2,
    ) -> ExecutionReport:
        """
        Submit order (simulate execution)

        Args:
            order: Order to execute
            current_bar: Current price bar
            slippage_bps: Slippage in basis points
            fee_bps: Fee in basis points

        Returns:
            Execution report
        """
        self.orders[order.order_id] = order

        # Simulate fill price with slippage
        if order.side == "buy":
            fill_price = current_bar.close * (1 + slippage_bps / 10000)
        else:  # sell
            fill_price = current_bar.close * (1 - slippage_bps / 10000)

        # Calculate commission
        notional = order.quantity * fill_price
        commission = notional * (fee_bps / 10000)

        # Update order status
        order.status = "filled"
        order.filled_price = fill_price
        order.filled_time = current_bar.ts

        # Create execution report
        report = ExecutionReport(
            order_id=order.order_id,
            status="filled",
            filled_quantity=order.quantity,
            filled_price=fill_price,
            commission=commission,
            timestamp=current_bar.ts,
        )

        self.execution_history.append(report)

        # Update capital
        if order.side == "buy":
            self.capital -= notional + commission
        else:  # sell
            self.capital += notional - commission

        return report

    def get_positions(self) -> List[Position]:
        """Get all current positions"""
        return list(self.positions.values())

    def add_position(self, position: Position):
        """Add a new position"""
        self.positions[position.ticker] = position

    def remove_position(self, ticker: str) -> Optional[Position]:
        """Remove and return a position"""
        return self.positions.pop(ticker, None)

    def get_capital(self) -> float:
        """Get current capital"""
        return self.capital

    def get_total_exposure(self) -> float:
        """Get total exposure across all positions"""
        return sum(pos.quantity * pos.entry_price for pos in self.positions.values())


# python/valuecell_trader/execution/orders.py
"""
Order creation and management
"""
from typing import Optional
import uuid
from datetime import datetime

from ..storage.schemas import Order, Allocation, PriceBar


class OrderManager:
    """Manage order creation"""

    def create_entry_order(
        self, allocation: Allocation, current_bar: PriceBar, max_spread_bps: float = 15
    ) -> Optional[Order]:
        """
        Create an entry order from allocation

        Args:
            allocation: Position allocation
            current_bar: Current price bar
            max_spread_bps: Maximum acceptable spread

        Returns:
            Order or None if should skip
        """
        # Check spread
        if current_bar.spread_bps and current_bar.spread_bps > max_spread_bps:
            return None

        # Calculate quantity
        quantity = allocation.target_notional / current_bar.close

        if quantity <= 0:
            return None

        # Create limit order with small buffer
        limit_price = current_bar.close * 1.001  # 0.1% above market

        order = Order(
            order_id=str(uuid.uuid4()),
            ticker=allocation.ticker,
            side="buy",
            quantity=quantity,
            order_type="limit",
            limit_price=limit_price,
            status="pending",
        )

        return order

    def create_exit_order(
        self, ticker: str, quantity: float, current_bar: PriceBar
    ) -> Order:
        """
        Create an exit order

        Args:
            ticker: Ticker symbol
            quantity: Quantity to sell
            current_bar: Current price bar

        Returns:
            Order
        """
        # Create market sell order
        order = Order(
            order_id=str(uuid.uuid4()),
            ticker=ticker,
            side="sell",
            quantity=quantity,
            order_type="market",
            status="pending",
        )

        return order
