#!/usr/bin/env python3
"""
VALUECELL AI TRADER - SIMPLE ALL-IN-ONE DEMO
Save this file and run: python simple_trader_demo.py

This is a standalone demo that doesn't require the full installation.
It shows how the system works with simplified versions of the components.
"""

import random
from datetime import datetime, timedelta
from typing import List, Dict, Any
import json

print("=" * 70)
print("VALUECELL AI TRADER - DEMO")
print("=" * 70)
print()


# ============================================================================
# SIMPLIFIED MODELS
# ============================================================================


class SimplePUp:
    """Simple conviction probability model"""

    def predict(self, sentiment: float, rsi: float, volume_ratio: float) -> float:
        score = 0.5
        score += sentiment * 0.2
        if rsi < 30:
            score += 0.15
        elif rsi > 70:
            score -= 0.15
        if volume_ratio > 2:
            score += 0.1
        return max(0, min(1, score))


class SimpleDExt:
    """Simple extension dampener"""

    def compute(self, rsi: float, z_score: float) -> float:
        dampener = 1.0
        if rsi > 75:
            dampener *= 0.5
        if z_score > 1.5:
            dampener *= 0.8
        return dampener


class SimplePDrop:
    """Simple downside probability"""

    def predict(self, sentiment: float, spread: float) -> float:
        prob = 0.1
        if sentiment < -0.3:
            prob += 0.3
        if spread > 15:
            prob += 0.2
        return min(1, prob)


class SimpleEnsemble:
    """Simple ensemble scorer"""

    def __init__(self):
        self.p_up = SimplePUp()
        self.d_ext = SimpleDExt()
        self.p_drop = SimplePDrop()

    def score(self, features: Dict[str, Any]) -> Dict[str, Any]:
        p_up = self.p_up.predict(
            features["sentiment"], features["rsi"], features["volume_ratio"]
        )
        d_ext = self.d_ext.compute(features["rsi"], features["z_score"])
        p_drop = self.p_drop.predict(features["sentiment"], features["spread"])

        s_final = p_up * d_ext * (1 - p_drop)

        if s_final >= 0.65:
            action = "BUY"
        elif s_final <= 0.35:
            action = "SELL"
        else:
            action = "HOLD"

        return {
            "s_final": s_final,
            "p_up": p_up,
            "d_ext": d_ext,
            "p_drop": p_drop,
            "action": action,
        }


# ============================================================================
# SIMPLE BROKER
# ============================================================================


class SimpleBroker:
    """Simple paper trading broker"""

    def __init__(self, capital: float = 1000):
        self.capital = capital
        self.initial_capital = capital
        self.positions = {}
        self.trades = []

    def buy(self, ticker: str, quantity: float, price: float):
        cost = quantity * price * 1.001  # 0.1% slippage
        if cost <= self.capital:
            self.capital -= cost
            self.positions[ticker] = {
                "quantity": quantity,
                "entry_price": price,
                "entry_time": datetime.now(),
            }
            print(f"  ✓ BOUGHT {quantity:.2f} shares of {ticker} @ ${price:.2f}")
        else:
            print(f"  ✗ Insufficient capital for {ticker}")

    def sell(self, ticker: str, price: float):
        if ticker in self.positions:
            pos = self.positions[ticker]
            proceeds = pos["quantity"] * price * 0.999  # 0.1% slippage
            pnl = proceeds - (pos["quantity"] * pos["entry_price"])
            self.capital += proceeds

            self.trades.append(
                {
                    "ticker": ticker,
                    "pnl": pnl,
                    "pnl_pct": (pnl / (pos["quantity"] * pos["entry_price"])) * 100,
                    "hold_time": (datetime.now() - pos["entry_time"]).total_seconds()
                    / 3600,
                }
            )

            print(f"  ✓ SOLD {pos['quantity']:.2f} shares of {ticker} @ ${price:.2f}")
            print(
                f"    P&L: ${pnl:+.2f} ({pnl / (pos['quantity'] * pos['entry_price']) * 100:+.2f}%)"
            )

            del self.positions[ticker]
        else:
            print(f"  ✗ No position in {ticker}")

    def get_total_equity(self, prices: Dict[str, float]) -> float:
        equity = self.capital
        for ticker, pos in self.positions.items():
            equity += pos["quantity"] * prices.get(ticker, pos["entry_price"])
        return equity

    def get_stats(self):
        if not self.trades:
            return None

        wins = [t for t in self.trades if t["pnl"] > 0]
        losses = [t for t in self.trades if t["pnl"] < 0]

        return {
            "total_trades": len(self.trades),
            "win_rate": len(wins) / len(self.trades) * 100,
            "avg_win": sum(t["pnl"] for t in wins) / len(wins) if wins else 0,
            "avg_loss": sum(t["pnl"] for t in losses) / len(losses) if losses else 0,
            "total_pnl": sum(t["pnl"] for t in self.trades),
        }


# ============================================================================
# DEMO SCENARIO
# ============================================================================


def run_demo():
    """Run a simplified trading demo"""

    print("SCENARIO: Trading 5 stocks over a simulated period")
    print()

    # Initialize
    ensemble = SimpleEnsemble()
    broker = SimpleBroker(capital=1000)

    tickers = ["AAPL", "MSFT", "NVDA", "META", "GOOGL"]
    prices = {t: 100 + random.uniform(-20, 20) for t in tickers}

    print(f"Starting Capital: ${broker.capital:.2f}")
    print()

    # Simulate 10 trading periods
    for period in range(1, 11):
        print(f"{'=' * 70}")
        print(f"PERIOD {period}")
        print(f"{'=' * 70}")

        # Update prices (random walk)
        for ticker in tickers:
            change = random.gauss(0, 0.03)
            prices[ticker] *= 1 + change

        # Evaluate each ticker
        for ticker in tickers:
            # Generate random features (in real system, these come from data)
            features = {
                "sentiment": random.gauss(0, 0.3),
                "rsi": random.uniform(30, 70),
                "volume_ratio": random.uniform(0.5, 3),
                "z_score": random.gauss(0, 1),
                "spread": random.uniform(3, 10),
            }

            # Score
            result = ensemble.score(features)

            print(f"\n{ticker} @ ${prices[ticker]:.2f}")
            print(
                f"  Score: {result['s_final']:.3f} (P_up={result['p_up']:.2f}, "
                f"D_ext={result['d_ext']:.2f}, P_drop={result['p_drop']:.2f})"
            )
            print(f"  Action: {result['action']}")

            # Execute action
            has_position = ticker in broker.positions

            if result["action"] == "BUY" and not has_position:
                # Size position (5% of capital)
                notional = broker.capital * 0.05
                quantity = notional / prices[ticker]
                broker.buy(ticker, quantity, prices[ticker])

            elif result["action"] == "SELL" and has_position:
                broker.sell(ticker, prices[ticker])

            elif has_position:
                # Check stop loss / take profit
                pos = broker.positions[ticker]
                pnl_pct = (prices[ticker] / pos["entry_price"] - 1) * 100

                if pnl_pct <= -2:  # 2% stop loss
                    print(f"  🛑 Stop loss triggered ({pnl_pct:.1f}%)")
                    broker.sell(ticker, prices[ticker])
                elif pnl_pct >= 4:  # 4% take profit
                    print(f"  🎯 Take profit triggered ({pnl_pct:.1f}%)")
                    broker.sell(ticker, prices[ticker])

        # Show portfolio status
        equity = broker.get_total_equity(prices)
        print(f"\n{'─' * 70}")
        print(
            f"Portfolio: ${equity:.2f} (Cash: ${broker.capital:.2f}, "
            f"Positions: {len(broker.positions)})"
        )
        print(f"Return: {(equity / broker.initial_capital - 1) * 100:+.2f}%")
        print()

        # Small delay for readability
        import time

        time.sleep(0.5)

    # Final results
    print(f"\n{'=' * 70}")
    print("FINAL RESULTS")
    print(f"{'=' * 70}")

    final_equity = broker.get_total_equity(prices)
    total_return = (final_equity / broker.initial_capital - 1) * 100

    print(f"\nInitial Capital: ${broker.initial_capital:.2f}")
    print(f"Final Equity:    ${final_equity:.2f}")
    print(f"Total Return:    {total_return:+.2f}%")

    stats = broker.get_stats()
    if stats:
        print(f"\nTrade Statistics:")
        print(f"  Total Trades:  {stats['total_trades']}")
        print(f"  Win Rate:      {stats['win_rate']:.1f}%")
        print(f"  Avg Win:       ${stats['avg_win']:.2f}")
        print(f"  Avg Loss:      ${stats['avg_loss']:.2f}")
        print(f"  Total P&L:     ${stats['total_pnl']:+.2f}")

    print(f"\n{'=' * 70}")
    print("Demo Complete!")
    print(f"{'=' * 70}")
    print()
    print("This was a SIMPLIFIED demo. The full system includes:")
    print("  • Real data ingestion from EDGAR, news feeds, social media")
    print("  • Trained ML models for P_up, P_drop, R_vol")
    print("  • Time-capsule backtesting with no look-ahead bias")
    print("  • REST APIs for integration")
    print("  • Real-time monitoring and alerts")
    print()


if __name__ == "__main__":
    run_demo()
