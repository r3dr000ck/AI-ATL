# python/valuecell_trader/backtest/engine.py
"""
Time-capsule backtesting engine
Ensures no look-ahead bias
"""
from typing import List, Dict, Optional
from datetime import datetime, timedelta
import numpy as np
import pandas as pd

from ..storage.schemas import (
    PriceBar,
    TextEvent,
    Position,
    Trade,
    BacktestReport,
    Features,
)
from ..config.schema import TraderConfig
from ..features.text_features import TextFeatureBuilder
from ..features.market_features import MarketFeatureBuilder
from ..models.__init__ import PUpModel
from ..models.d_ext import DExtModel
from ..models.model_trainer import PDropModel
from ..execution.sizing import PositionSizer
from ..execution.risk import RiskManager
from ..execution.broker_paper import PaperBroker
from ..execution.orders import OrderManager


class BacktestEngine:
    """
    Time-capsule backtesting engine
    Simulates trading with strict no-look-ahead rules
    """

    def __init__(self, config: TraderConfig):
        self.config = config

        # Initialize components
        self.text_features = TextFeatureBuilder()
        self.market_features = MarketFeatureBuilder()
        self.p_up_model = PUpModel()
        self.d_ext_model = DExtModel(
            alpha=config.scoring.alpha_ext,
            z_threshold=config.scoring.z_threshold,
            rsi_overbought=config.scoring.rsi_overbought,
            volume_spike_mult=config.scoring.volume_spike_mult,
        )
        self.p_drop_model = PDropModel()

        self.sizer = PositionSizer(config.risk)
        self.risk_manager = RiskManager(config.risk)
        self.order_manager = OrderManager()

        # EMA smoothing parameter
        self.beta = 0.3
        self.prev_s_final: Dict[str, float] = {}

    def run_backtest(
        self,
        start_ts: datetime,
        end_ts: datetime,
        bars_data: Dict[str, List[PriceBar]],
        events_data: List[TextEvent],
        initial_capital: float = 1000.0,
    ) -> BacktestReport:
        """
        Run time-capsule backtest

        Args:
            start_ts: Backtest start time
            end_ts: Backtest end time
            bars_data: Dict of ticker -> list of price bars
            events_data: List of all text events
            initial_capital: Starting capital

        Returns:
            Backtest report with results
        """
        # Initialize broker
        broker = PaperBroker(initial_capital)

        # Storage
        completed_trades: List[Trade] = []
        equity_curve = []

        # Get all timestamps (union of all bar timestamps)
        all_timestamps = set()
        for bars in bars_data.values():
            all_timestamps.update([bar.ts for bar in bars])
        timestamps = sorted(list(all_timestamps))

        # Filter timestamps to backtest window
        timestamps = [ts for ts in timestamps if start_ts <= ts <= end_ts]

        print(f"Starting backtest from {start_ts} to {end_ts}")
        print(f"Processing {len(timestamps)} timestamps")

        # Main simulation loop
        for i, current_ts in enumerate(timestamps):
            if i % 100 == 0:
                print(
                    f"Progress: {i}/{len(timestamps)} ({i / len(timestamps) * 100:.1f}%)"
                )

            # Get visible events (with latency)
            visible_events = self._get_visible_events(events_data, current_ts)

            # Process each ticker
            for ticker in self.config.universe.tickers:
                if ticker not in bars_data:
                    continue

                # Get historical bars up to current time
                hist_bars = [bar for bar in bars_data[ticker] if bar.ts <= current_ts]

                if len(hist_bars) < 30:  # Need enough history
                    continue

                current_bar = hist_bars[-1]

                # Check if we have a position
                positions = broker.get_positions()
                existing_position = next(
                    (p for p in positions if p.ticker == ticker), None
                )

                if existing_position:
                    # Manage existing position
                    self._manage_position(
                        existing_position,
                        current_bar,
                        current_ts,
                        hist_bars,
                        visible_events,
                        broker,
                        completed_trades,
                    )
                else:
                    # Evaluate new entry
                    self._evaluate_entry(
                        ticker,
                        current_bar,
                        current_ts,
                        hist_bars,
                        visible_events,
                        broker,
                    )

            # Record equity
            total_equity = broker.get_capital()
            for position in broker.get_positions():
                # Mark to market
                hist_bars = [
                    b for b in bars_data[position.ticker] if b.ts <= current_ts
                ]
                if hist_bars:
                    current_price = hist_bars[-1].close
                    total_equity += position.quantity * current_price

            equity_curve.append({"timestamp": current_ts, "equity": total_equity})

        print(f"Backtest complete. Final capital: ${broker.get_capital():.2f}")
        print(f"Number of trades: {len(completed_trades)}")

        # Calculate metrics
        report = self._calculate_metrics(
            initial_capital, equity_curve, completed_trades, start_ts, end_ts
        )

        return report

    def _get_visible_events(
        self, all_events: List[TextEvent], current_ts: datetime
    ) -> List[TextEvent]:
        """
        Get events visible at current time (with latency)

        Applies SIM_LATENCY_SECONDS delay
        """
        latency = timedelta(seconds=self.config.sim_latency_seconds)

        visible = []
        for event in all_events:
            # Event visible after: max(published_at, first_seen_at) + latency
            visible_at = max(event.published_at, event.first_seen_at) + latency

            if visible_at <= current_ts:
                visible.append(event)

        return visible

    def _evaluate_entry(
        self,
        ticker: str,
        current_bar: PriceBar,
        current_ts: datetime,
        hist_bars: List[PriceBar],
        visible_events: List[TextEvent],
        broker: PaperBroker,
    ):
        """Evaluate potential new entry"""
        # Build features
        text_feat = self.text_features.build_features(
            ticker, current_ts, visible_events
        )
        market_feat = self.market_features.build_features(
            ticker, hist_bars[:-1], current_bar
        )

        features = {**text_feat, **market_feat}

        # Calculate scores
        p_up = self.p_up_model.predict(features)
        d_ext = self.d_ext_model.compute(features)
        p_drop = self.p_drop_model.predict(features)

        # Calculate raw score
        s_raw = p_up * d_ext * (1 - p_drop)

        # Apply EMA smoothing
        prev = self.prev_s_final.get(ticker, 0.5)
        s_final = (1 - self.beta) * prev + self.beta * s_raw
        self.prev_s_final[ticker] = s_final

        # Check entry threshold
        if s_final < self.config.scoring.enter_threshold:
            return

        # Size position
        current_exposures = {
            p.ticker: p.quantity * p.entry_price for p in broker.get_positions()
        }

        allocation = self.sizer.size_position(
            ticker,
            s_final,
            broker.get_capital() + broker.get_total_exposure(),
            current_exposures,
        )

        if not allocation or allocation.target_notional <= 0:
            return

        # Create order
        order = self.order_manager.create_entry_order(allocation, current_bar)
        if not order:
            return

        # Execute order
        report = broker.submit_order(
            order,
            current_bar,
            self.config.simulation.slippage_bps,
            self.config.simulation.fee_bps,
        )

        if report.status == "filled":
            # Calculate stops
            atr = market_feat.get("atr")
            stop_price, tp_price = self.risk_manager.calculate_stops(
                report.filled_price, atr
            )

            # Create position
            position = Position(
                ticker=ticker,
                entry_price=report.filled_price,
                quantity=report.filled_quantity,
                entry_time=current_ts,
                stop_price=stop_price,
                tp_price=tp_price,
                timeout_time=current_ts + timedelta(days=self.config.risk.timeout_days),
                s_final_entry=s_final,
            )

            broker.add_position(position)

    def _manage_position(
        self,
        position: Position,
        current_bar: PriceBar,
        current_ts: datetime,
        hist_bars: List[PriceBar],
        visible_events: List[TextEvent],
        broker: PaperBroker,
        completed_trades: List[Trade],
    ):
        """Manage existing position"""
        # Build features for exit decision
        text_feat = self.text_features.build_features(
            position.ticker, current_ts, visible_events
        )
        market_feat = self.market_features.build_features(
            position.ticker, hist_bars[:-1], current_bar
        )

        features = {**text_feat, **market_feat}
        p_drop = self.p_drop_model.predict(features)

        # Check exits
        exit_reason = self.risk_manager.check_exits(
            position, current_bar, current_ts, p_drop
        )

        if exit_reason:
            # Create exit order
            order = self.order_manager.create_exit_order(
                position.ticker, position.quantity, current_bar
            )

            # Execute exit
            report = broker.submit_order(
                order,
                current_bar,
                self.config.simulation.slippage_bps,
                self.config.simulation.fee_bps,
            )

            if report.status == "filled":
                # Calculate P&L
                pnl = (report.filled_price - position.entry_price) * position.quantity
                pnl_pct = (report.filled_price / position.entry_price - 1) * 100

                # Record trade
                trade = Trade(
                    trade_id=f"{position.ticker}_{position.entry_time.isoformat()}",
                    ticker=position.ticker,
                    entry_time=position.entry_time,
                    exit_time=current_ts,
                    entry_price=position.entry_price,
                    exit_price=report.filled_price,
                    quantity=position.quantity,
                    pnl=pnl,
                    pnl_pct=pnl_pct,
                    exit_reason=exit_reason,
                    s_final_entry=position.s_final_entry,
                )

                completed_trades.append(trade)
                broker.remove_position(position.ticker)

    def _calculate_metrics(
        self,
        initial_capital: float,
        equity_curve: List[Dict],
        trades: List[Trade],
        start_ts: datetime,
        end_ts: datetime,
    ) -> BacktestReport:
        """Calculate backtest metrics"""
        if not equity_curve:
            return self._empty_report(initial_capital, start_ts, end_ts)

        df = pd.DataFrame(equity_curve)
        final_capital = df["equity"].iloc[-1]

        # Calculate returns
        total_return = (final_capital / initial_capital - 1) * 100

        # CAGR
        days = (end_ts - start_ts).days
        years = days / 365.25
        cagr = (
            ((final_capital / initial_capital) ** (1 / years) - 1) * 100
            if years > 0
            else 0
        )

        # Sharpe ratio
        df["returns"] = df["equity"].pct_change()
        sharpe = (
            (df["returns"].mean() / df["returns"].std() * np.sqrt(252))
            if df["returns"].std() > 0
            else 0
        )

        # Sortino ratio
        downside_returns = df["returns"][df["returns"] < 0]
        sortino = (
            df["returns"].mean() / downside_returns.std() * np.sqrt(252)
            if len(downside_returns) > 0 and downside_returns.std() > 0
            else 0
        )

        # Max drawdown
        cummax = df["equity"].cummax()
        drawdown = (df["equity"] - cummax) / cummax
        max_dd = drawdown.min() * 100

        # Trade statistics
        if trades:
            wins = [t for t in trades if t.pnl > 0]
            losses = [t for t in trades if t.pnl < 0]

            win_rate = len(wins) / len(trades) * 100
            avg_win = np.mean([t.pnl for t in wins]) if wins else 0
            avg_loss = np.mean([t.pnl for t in losses]) if losses else 0
        else:
            win_rate = 0
            avg_win = 0
            avg_loss = 0

        # Turnover (simplified)
        turnover = len(trades)

        # Calibration metrics (placeholder)
        brier_score = 0.0
        reliability_bins = {}

        return BacktestReport(
            start_time=start_ts,
            end_time=end_ts,
            initial_capital=initial_capital,
            final_capital=final_capital,
            total_return=total_return,
            cagr=cagr,
            sharpe=sharpe,
            sortino=sortino,
            max_drawdown=max_dd,
            win_rate=win_rate,
            avg_win=avg_win,
            avg_loss=avg_loss,
            num_trades=len(trades),
            turnover=turnover,
            trades=trades,
            brier_score=brier_score,
            reliability_bins=reliability_bins,
        )

    def _empty_report(
        self, initial_capital: float, start_ts: datetime, end_ts: datetime
    ) -> BacktestReport:
        """Return empty report when no data"""
        return BacktestReport(
            start_time=start_ts,
            end_time=end_ts,
            initial_capital=initial_capital,
            final_capital=initial_capital,
            total_return=0.0,
            cagr=0.0,
            sharpe=0.0,
            sortino=0.0,
            max_drawdown=0.0,
            win_rate=0.0,
            avg_win=0.0,
            avg_loss=0.0,
            num_trades=0,
            turnover=0.0,
            trades=[],
            brier_score=0.0,
            reliability_bins={},
        )
