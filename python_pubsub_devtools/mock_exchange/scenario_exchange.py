#!/usr/bin/env python3
"""
Scenario-Based Mock Exchange - Realistic Market Simulation

Provides a mock exchange that simulates various market scenarios for testing:
- Bull runs, bear crashes, sideways markets
- Flash crashes, high volatility
- Irregular candles (for testing error handling)
"""
import math
import random
from dataclasses import dataclass
from datetime import datetime, timezone, timedelta
from enum import Enum
from typing import Dict, Any

import pandas as pd


class MarketScenario(Enum):
    """Predefined market scenarios for testing"""
    BULL_RUN = "bull_run"  # Steady uptrend +20% over 100 candles
    BEAR_CRASH = "bear_crash"  # Downtrend -30% over 50 candles
    SIDEWAYS = "sideways"  # ±2% oscillation around base price
    FLASH_CRASH = "flash_crash"  # Sudden -15% drop then recovery
    VOLATILE = "volatile"  # High variance ±5% per candle
    IRREGULAR_CANDLES = "irregular_candles"  # Gaps in timestamps
    DEAD_CAT_BOUNCE = "dead_cat_bounce"  # Drop, bounce, continue drop
    PUMP_AND_DUMP = "pump_and_dump"  # Quick rise then crash
    ACCUMULATION = "accumulation"  # Tight range before breakout
    DISTRIBUTION = "distribution"  # Tight range before breakdown


@dataclass
class MarketPriceData:
    """Container for market price data"""
    current_price: Any  # Price object
    buy_price: Any  # Price object (slightly higher)
    sell_price: Any  # Price object (slightly lower)
    candlesticks: pd.DataFrame
    timestamp: str


class ScenarioBasedMockExchange:
    """Mock exchange that simulates realistic market scenarios

    Usage:
        exchange = ScenarioBasedMockExchange(
            scenario=MarketScenario.BULL_RUN,
            initial_price=50000.0,
            pair="BTC/USDT"
        )

        price_data = exchange.fetch_current_price()
    """

    def __init__(
            self,
            scenario: MarketScenario,
            initial_price: float = 50000.0,
            pair: str = "BTC/USDT",
            candle_count: int = 100,
            volatility_multiplier: float = 1.0,
            spread_bps: int = 20  # Spread in basis points (20 = 0.2%)
    ):
        """Initialize mock exchange with scenario

        Args:
            scenario: Market scenario to simulate
            initial_price: Starting price
            pair: Trading pair (e.g., "BTC/USDT")
            candle_count: Number of historical candles to generate
            volatility_multiplier: Multiplier for price volatility (1.0 = normal)
            spread_bps: Bid-ask spread in basis points
        """
        self.scenario = scenario
        self.initial_price = initial_price
        self.current_price = initial_price
        self.pair = pair
        self.candle_count = candle_count
        self.volatility_multiplier = volatility_multiplier
        self.spread_bps = spread_bps

        # Track state
        self.call_count = 0
        self.price_history = [initial_price]

        # Market state (for realistic order book simulation)
        self.balances = {
            "USDT": 100000.0,
            "BTC": 0.0
        }

        # Generate initial candles
        self._historical_candles = self._generate_historical_candles()

    def fetch_current_price(self) -> MarketPriceData:
        """Fetch current market price based on scenario

        Returns:
            MarketPriceData with current price, buy/sell prices, and candles
        """
        self.call_count += 1

        # Generate next price based on scenario
        self.current_price = self._generate_next_price()
        self.price_history.append(self.current_price)

        # Calculate bid-ask spread
        spread = self.current_price * (self.spread_bps / 10000)
        buy_price = self.current_price + spread / 2
        sell_price = self.current_price - spread / 2

        # Update candles with new data
        self._update_candles()

        # Create price objects (mock)
        from unittest.mock import Mock

        current_price_obj = Mock()
        current_price_obj.price = self.current_price

        buy_price_obj = Mock()
        buy_price_obj.price = buy_price

        sell_price_obj = Mock()
        sell_price_obj.price = sell_price

        return MarketPriceData(
            current_price=current_price_obj,
            buy_price=buy_price_obj,
            sell_price=sell_price_obj,
            candlesticks=self._historical_candles.copy(),
            timestamp=datetime.now(timezone.utc).isoformat()
        )

    def _generate_next_price(self) -> float:
        """Generate next price based on scenario"""

        if self.scenario == MarketScenario.BULL_RUN:
            # Linear growth with noise: +20% over 100 candles = +0.2% per candle
            trend = 1.002
            noise = random.uniform(0.998, 1.002)
            return self.current_price * trend * noise

        elif self.scenario == MarketScenario.BEAR_CRASH:
            # Exponential decay: -30% over 50 candles
            if self.call_count <= 50:
                decay_rate = 0.993  # ~-0.7% per candle
                noise = random.uniform(0.995, 1.005)
                return self.current_price * decay_rate * noise
            else:
                # Stabilize after crash
                noise = random.uniform(0.999, 1.001)
                return self.current_price * noise

        elif self.scenario == MarketScenario.SIDEWAYS:
            # Oscillation around initial price: ±2%
            phase = self.call_count / 10
            oscillation = 1 + 0.02 * math.sin(phase)
            noise = random.uniform(0.999, 1.001)
            return self.initial_price * oscillation * noise

        elif self.scenario == MarketScenario.FLASH_CRASH:
            # Sudden drop at candle 20, recovery by candle 30
            if 20 <= self.call_count < 30:
                # Flash crash: -15%
                return self.initial_price * 0.85 * random.uniform(0.99, 1.01)
            elif 30 <= self.call_count < 50:
                # Recovery phase: gradually back to initial
                progress = (self.call_count - 30) / 20  # 0.0 to 1.0
                target = self.initial_price * 0.85 + (self.initial_price - self.initial_price * 0.85) * progress
                return target * random.uniform(0.995, 1.005)
            else:
                # Back to normal, oscillate around initial
                noise = random.uniform(0.998, 1.002)
                return self.initial_price * noise

        elif self.scenario == MarketScenario.VOLATILE:
            # High volatility: ±5% per candle
            change = random.uniform(0.95, 1.05) * self.volatility_multiplier
            return self.current_price * change

        elif self.scenario == MarketScenario.IRREGULAR_CANDLES:
            # Normal price movement (irregularity is in timestamps)
            noise = random.uniform(0.998, 1.002)
            return self.current_price * noise

        elif self.scenario == MarketScenario.DEAD_CAT_BOUNCE:
            # Drop 20%, bounce 10%, continue down 15%
            if self.call_count <= 15:
                return self.current_price * 0.987  # Drop phase
            elif 15 < self.call_count <= 25:
                return self.current_price * 1.008  # Bounce phase
            else:
                return self.current_price * 0.992  # Continue drop

        elif self.scenario == MarketScenario.PUMP_AND_DUMP:
            # Quick +30% in 20 candles, then -40% crash
            if self.call_count <= 20:
                return self.current_price * 1.013  # Pump: ~+30%
            elif 20 < self.call_count <= 35:
                return self.current_price * 0.973  # Dump: ~-40%
            else:
                return self.current_price * random.uniform(0.999, 1.001)

        elif self.scenario == MarketScenario.ACCUMULATION:
            # Tight range ±1% for 50 candles, then breakout +15%
            if self.call_count <= 50:
                return self.initial_price * random.uniform(0.99, 1.01)
            else:
                return self.current_price * 1.003  # Breakout

        elif self.scenario == MarketScenario.DISTRIBUTION:
            # Tight range ±1% for 50 candles, then breakdown -15%
            if self.call_count <= 50:
                return self.initial_price * random.uniform(0.99, 1.01)
            else:
                return self.current_price * 0.997  # Breakdown

        else:
            # Default: random walk
            return self.current_price * random.uniform(0.998, 1.002)

    def _generate_historical_candles(self) -> pd.DataFrame:
        """Generate historical OHLCV candles"""
        candles = []
        price = self.initial_price

        for i in range(self.candle_count):
            # Simulate price movement
            open_price = price

            # Generate realistic OHLC
            high_low_range = price * 0.02 * self.volatility_multiplier  # 2% range
            high_price = open_price + random.uniform(0, high_low_range)
            low_price = open_price - random.uniform(0, high_low_range)

            # Close price biased towards high/low based on scenario
            if self.scenario == MarketScenario.BULL_RUN:
                close_price = random.uniform(open_price, high_price)
            elif self.scenario == MarketScenario.BEAR_CRASH:
                close_price = random.uniform(low_price, open_price)
            else:
                close_price = random.uniform(low_price, high_price)

            # Ensure OHLC logic: H >= O,C,L and L <= O,C,H
            high_price = max(high_price, open_price, close_price)
            low_price = min(low_price, open_price, close_price)

            # Volume: random with some correlation to volatility
            volume = random.uniform(50, 500) * (1 + abs(close_price - open_price) / open_price * 10)

            # Timestamp
            base_time = datetime.now(timezone.utc) - timedelta(minutes=self.candle_count - i)
            timestamp_ms = int(base_time.timestamp() * 1000)

            # IRREGULAR_CANDLES: introduce gaps
            if self.scenario == MarketScenario.IRREGULAR_CANDLES and i % 10 == 5:
                timestamp_ms += 30000  # Add 30s gap = irregular interval

            candles.append([timestamp_ms, open_price, high_price, low_price, close_price, volume])

            price = close_price  # Next candle starts from this close

        df = pd.DataFrame(candles, columns=["timestamp", "open", "high", "low", "close", "volume"])
        return df

    def _update_candles(self):
        """Update candles DataFrame with latest price"""
        # Remove oldest candle
        self._historical_candles = self._historical_candles.iloc[1:].copy()

        # Add new candle
        open_price = self.price_history[-2] if len(self.price_history) > 1 else self.current_price
        close_price = self.current_price

        # Generate OHLC
        high_low_range = self.current_price * 0.01
        high_price = max(open_price, close_price) + random.uniform(0, high_low_range)
        low_price = min(open_price, close_price) - random.uniform(0, high_low_range)

        volume = random.uniform(50, 500)

        timestamp_ms = int(datetime.now(timezone.utc).timestamp() * 1000)

        # IRREGULAR_CANDLES: sometimes add gap
        if self.scenario == MarketScenario.IRREGULAR_CANDLES and self.call_count % 10 == 5:
            timestamp_ms += 30000

        new_candle = pd.DataFrame([
            [timestamp_ms, open_price, high_price, low_price, close_price, volume]
        ], columns=["timestamp", "open", "high", "low", "close", "volume"])

        self._historical_candles = pd.concat([self._historical_candles, new_candle], ignore_index=True)

    def get_price_statistics(self) -> Dict[str, float]:
        """Get statistics about price movement

        Returns:
            Dict with min, max, mean, volatility, total_return
        """
        prices = self.price_history

        return {
            "min_price": min(prices),
            "max_price": max(prices),
            "mean_price": sum(prices) / len(prices),
            "volatility": self._calculate_volatility(prices),
            "total_return_pct": ((prices[-1] - prices[0]) / prices[0]) * 100,
            "call_count": self.call_count
        }

    def _calculate_volatility(self, prices) -> float:
        """Calculate price volatility (standard deviation of returns)"""
        if len(prices) < 2:
            return 0.0

        returns = [(prices[i] - prices[i - 1]) / prices[i - 1] for i in range(1, len(prices))]
        mean_return = sum(returns) / len(returns)
        variance = sum((r - mean_return) ** 2 for r in returns) / len(returns)
        return math.sqrt(variance)

    def reset(self):
        """Reset exchange to initial state"""
        self.current_price = self.initial_price
        self.call_count = 0
        self.price_history = [self.initial_price]
        self._historical_candles = self._generate_historical_candles()


def main():
    """CLI interface for testing scenarios"""
    import argparse

    parser = argparse.ArgumentParser(description="Scenario-Based Mock Exchange")
    parser.add_argument('--scenario', type=str, default='bull_run',
                        choices=[s.value for s in MarketScenario],
                        help='Market scenario to simulate')
    parser.add_argument('--calls', type=int, default=50,
                        help='Number of price fetches to simulate')
    parser.add_argument('--initial-price', type=float, default=50000.0,
                        help='Initial price')

    args = parser.parse_args()

    scenario = MarketScenario(args.scenario)
    exchange = ScenarioBasedMockExchange(
        scenario=scenario,
        initial_price=args.initial_price
    )

    print(f"\n{'=' * 80}")
    print(f"Simulating {scenario.value.upper()} scenario")
    print(f"Initial price: ${args.initial_price:,.2f}")
    print(f"{'=' * 80}\n")

    for i in range(args.calls):
        price_data = exchange.fetch_current_price()
        print(f"Call {i + 1:3d}: ${price_data.current_price.price:,.2f}")

    print(f"\n{'=' * 80}")
    print("Statistics:")
    print(f"{'=' * 80}")

    stats = exchange.get_price_statistics()
    for key, value in stats.items():
        if 'price' in key:
            print(f"  {key:20s}: ${value:,.2f}")
        elif 'pct' in key:
            print(f"  {key:20s}: {value:+.2f}%")
        else:
            print(f"  {key:20s}: {value:.4f}")

    print(f"{'=' * 80}\n")


if __name__ == '__main__':
    main()
