# python/valuecell_trader/api/monitor_service.py
"""
Monitoring service API - Track system status and performance
"""
from fastapi import FastAPI
from pydantic import BaseModel
from typing import List, Dict, Any
from datetime import datetime, timedelta
import logging

from ..execution.broker_paper import PaperBroker
from ..storage.schemas import Trade

logger = logging.getLogger(__name__)


class PortfolioStatus(BaseModel):
    """Current portfolio status"""
    total_equity: float
    available_capital: float
    total_exposure: float
    exposure_pct: float
    num_positions: int
    positions: List[Dict[str, Any]]


class PerformanceMetrics(BaseModel):
    """Performance metrics"""
    total_return: float
    sharpe_ratio: float
    max_drawdown: float
    win_rate: float
    num_trades: int
    avg_win: float
    avg_loss: float


class MonitorService:
    """Service for monitoring system status"""

    def __init__(self, broker: PaperBroker, initial_capital: float = 1000.0):
        self.broker = broker
        self.initial_capital = initial_capital
        self.trade_history: List[Trade] = []

        self.app = FastAPI(title="ValueCell Trader - Monitor Service")
        self._setup_routes()

    def _setup_routes(self):
        """Setup FastAPI routes"""

        @self.app.get("/status", response_model=PortfolioStatus)
        async def get_status():
            """Get current portfolio status"""
            positions = self.broker.get_positions()
            total_exposure = self.broker.get_total_exposure()
            capital = self.broker.get_capital()
            total_equity = capital + total_exposure

            return PortfolioStatus(
                total_equity=total_equity,
                available_capital=capital,
                total_exposure=total_exposure,
                exposure_pct=(total_exposure / total_equity * 100) if total_equity > 0 else 0,
                num_positions=len(positions),
                positions=[{
                    'ticker': p.ticker,
                    'quantity': p.quantity,
                    'entry_price': p.entry_price,
                    'current_value': p.quantity * p.entry_price,  # Would be current_price in reality
                    'unrealized_pnl': 0,  # Would calculate from current price
                    'entry_time': p.entry_time.isoformat()
                } for p in positions]
            )

        @self.app.get("/performance", response_model=PerformanceMetrics)
        async def get_performance():
            """Get performance metrics"""
            if not self.trade_history:
                return PerformanceMetrics(
                    total_return=0,
                    sharpe_ratio=0,
                    max_drawdown=0,
                    win_rate=0,
                    num_trades=0,
                    avg_win=0,
                    avg_loss=0
                )

            # Calculate metrics
            total_pnl = sum(t.pnl for t in self.trade_history)
            total_return = (total_pnl / self.initial_capital) * 100

            wins = [t for t in self.trade_history if t.pnl > 0]
            losses = [t for t in self.trade_history if t.pnl < 0]

            win_rate = (len(wins) / len(self.trade_history) * 100) if self.trade_history else 0
            avg_win = sum(t.pnl for t in wins) / len(wins) if wins else 0
            avg_loss = sum(t.pnl for t in losses) / len(losses) if losses else 0

            # Simplified Sharpe (would need returns series for real calc)
            sharpe = 0.0

            # Simplified max DD
            max_dd = 0.0

            return PerformanceMetrics(
                total_return=total_return,
                sharpe_ratio=sharpe,
                max_drawdown=max_dd,
                win_rate=win_rate,
                num_trades=len(self.trade_history),
                avg_win=avg_win,
                avg_loss=avg_loss
            )

        @self.app.get("/trades")
        async def get_trades(limit: int = 50):
            """Get recent trade history"""
            recent = self.trade_history[-limit:]
            return {
                "trades": [t.dict() for t in recent],
                "total": len(self.trade_history)
            }

        @self.app.get("/health")
        async def health_check():
            """Health check endpoint"""
            return {
                "status": "healthy",
                "timestamp": datetime.now().isoformat(),
                "broker_capital": self.broker.get_capital(),
                "num_positions": len(self.broker.get_positions())
            }