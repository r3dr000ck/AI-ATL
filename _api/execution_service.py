# python/valuecell_trader/api/execution_service.py
"""
Execution service API - Handle trade execution requests
"""
from fastapi import FastAPI, HTTPException, BackgroundTasks
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from datetime import datetime
import logging

from ..execution.broker_paper import PaperBroker
from ..execution.sizing import PositionSizer
from ..execution.orders import OrderManager
from ..storage.schemas import Order, Position
from ..config.schema import TraderConfig

logger = logging.getLogger(__name__)


class TradeRequest(BaseModel):
    """Trade execution request"""

    ticker: str = Field(..., description="Ticker symbol")
    action: str = Field(..., description="BUY or SELL")
    s_final: Optional[float] = Field(None, ge=0, le=1, description="Investment score")
    quantity: Optional[float] = Field(
        None, gt=0, description="Optional quantity override"
    )
    reason: str = Field("manual", description="Reason for trade")


class TradeResponse(BaseModel):
    """Trade execution response"""

    success: bool
    order_id: Optional[str] = None
    ticker: str
    action: str
    quantity: float
    price: Optional[float] = None
    message: str
    timestamp: datetime


class ExecutionService:
    """Service for executing trades"""

    def __init__(self, config: TraderConfig, broker: PaperBroker):
        self.config = config
        self.broker = broker
        self.sizer = PositionSizer(config.risk)
        self.order_manager = OrderManager()
        self.app = FastAPI(title="ValueCell Trader - Execution Service")

        # Setup routes
        self._setup_routes()

    def _setup_routes(self):
        """Setup FastAPI routes"""

        @self.app.post("/trade", response_model=TradeResponse)
        async def execute_trade(request: TradeRequest):
            """
            Execute a trade

            Example:
            ```
            POST /trade
            {
                "ticker": "AAPL",
                "action": "BUY",
                "s_final": 0.65,
                "reason": "high_conviction_signal"
            }
            ```
            """
            try:
                if request.action.upper() == "BUY":
                    return await self._execute_buy(request)
                elif request.action.upper() == "SELL":
                    return await self._execute_sell(request)
                else:
                    raise HTTPException(400, f"Invalid action: {request.action}")

            except Exception as e:
                logger.error(f"Trade execution failed: {e}", exc_info=True)
                raise HTTPException(500, f"Execution failed: {str(e)}")

        @self.app.get("/positions")
        async def get_positions():
            """Get all current positions"""
            positions = self.broker.get_positions()
            return {
                "positions": [p.dict() for p in positions],
                "total_exposure": self.broker.get_total_exposure(),
                "capital": self.broker.get_capital(),
            }

        @self.app.get("/capital")
        async def get_capital_info():
            """Get capital information"""
            return {
                "available_capital": self.broker.get_capital(),
                "total_exposure": self.broker.get_total_exposure(),
                "total_equity": self.broker.get_capital()
                + self.broker.get_total_exposure(),
            }

    async def _execute_buy(self, request: TradeRequest) -> TradeResponse:
        """Execute buy order"""

        # Check if already have position
        positions = self.broker.get_positions()
        if any(p.ticker == request.ticker for p in positions):
            return TradeResponse(
                success=False,
                ticker=request.ticker,
                action="BUY",
                quantity=0,
                message=f"Already have position in {request.ticker}",
                timestamp=datetime.now(),
            )

        # Size position
        if request.quantity:
            target_notional = request.quantity * 100  # Assume $100 price
            from ..storage.schemas import Allocation

            allocation = Allocation(
                ticker=request.ticker,
                target_notional=target_notional,
                target_quantity=request.quantity,
                s_final=request.s_final or 0.6,
                reason=request.reason,
            )
        else:
            if not request.s_final:
                raise HTTPException(400, "Must provide either quantity or s_final")

            current_exposures = {
                p.ticker: p.quantity * p.entry_price for p in positions
            }

            capital = self.broker.get_capital() + self.broker.get_total_exposure()
            allocation = self.sizer.size_position(
                request.ticker, request.s_final, capital, current_exposures
            )

            if not allocation or allocation.target_notional <= 0:
                return TradeResponse(
                    success=False,
                    ticker=request.ticker,
                    action="BUY",
                    quantity=0,
                    message="Position size too small or caps exceeded",
                    timestamp=datetime.now(),
                )

        # Note: In real implementation, would get current price from market data
        # For now, use placeholder
        from ..storage.schemas import PriceBar

        current_bar = PriceBar(
            ticker=request.ticker,
            ts=datetime.now(),
            open=100,
            high=101,
            low=99,
            close=100,
            volume=1000000,
            vwap=100,
            spread_bps=5,
        )

        # Create and execute order
        order = self.order_manager.create_entry_order(allocation, current_bar)
        if not order:
            return TradeResponse(
                success=False,
                ticker=request.ticker,
                action="BUY",
                quantity=0,
                message="Order creation failed (spread too wide?)",
                timestamp=datetime.now(),
            )

        report = self.broker.submit_order(order, current_bar)

        if report.status == "filled":
            # Create position
            stop_price = report.filled_price * (1 - self.config.risk.stop_pct)
            tp_price = report.filled_price * (1 + self.config.risk.tp_pct)
            from datetime import timedelta

            position = Position(
                ticker=request.ticker,
                entry_price=report.filled_price,
                quantity=report.filled_quantity,
                entry_time=datetime.now(),
                stop_price=stop_price,
                tp_price=tp_price,
                timeout_time=datetime.now()
                + timedelta(days=self.config.risk.timeout_days),
                s_final_entry=request.s_final or 0.6,
            )

            self.broker.add_position(position)

            return TradeResponse(
                success=True,
                order_id=order.order_id,
                ticker=request.ticker,
                action="BUY",
                quantity=report.filled_quantity,
                price=report.filled_price,
                message=f"Buy order filled at ${report.filled_price:.2f}",
                timestamp=datetime.now(),
            )
        else:
            return TradeResponse(
                success=False,
                ticker=request.ticker,
                action="BUY",
                quantity=0,
                message=f"Order failed: {report.status}",
                timestamp=datetime.now(),
            )

    async def _execute_sell(self, request: TradeRequest) -> TradeResponse:
        """Execute sell order"""

        # Find position
        position = self.broker.positions.get(request.ticker)
        if not position:
            return TradeResponse(
                success=False,
                ticker=request.ticker,
                action="SELL",
                quantity=0,
                message=f"No position in {request.ticker}",
                timestamp=datetime.now(),
            )

        quantity = request.quantity or position.quantity

        # Create market data (placeholder)
        from ..storage.schemas import PriceBar

        current_bar = PriceBar(
            ticker=request.ticker,
            ts=datetime.now(),
            open=100,
            high=101,
            low=99,
            close=100,
            volume=1000000,
            vwap=100,
            spread_bps=5,
        )

        # Create and execute exit order
        order = self.order_manager.create_exit_order(
            request.ticker, quantity, current_bar
        )

        report = self.broker.submit_order(order, current_bar)

        if report.status == "filled":
            # Remove position if fully closed
            if quantity >= position.quantity:
                self.broker.remove_position(request.ticker)

            return TradeResponse(
                success=True,
                order_id=order.order_id,
                ticker=request.ticker,
                action="SELL",
                quantity=report.filled_quantity,
                price=report.filled_price,
                message=f"Sell order filled at ${report.filled_price:.2f}",
                timestamp=datetime.now(),
            )
        else:
            return TradeResponse(
                success=False,
                ticker=request.ticker,
                action="SELL",
                quantity=0,
                message=f"Order failed: {report.status}",
                timestamp=datetime.now(),
            )
