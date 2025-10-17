"""
Example Market Scenarios for Mock Exchange

Provides predefined market scenarios for testing trading strategies.
"""
from __future__ import annotations

import random
from typing import List, Dict, Any


def generate_trending_market(
        symbol: str = "BTC/USDT",
        initial_price: float = 50000.0,
        num_candles: int = 100,
        trend: float = 0.01
) -> List[Dict[str, Any]]:
    """
    Generate a trending market scenario.
    
    Args:
        symbol: Trading pair symbol
        initial_price: Starting price
        num_candles: Number of candlesticks to generate
        trend: Trend strength (0.01 = 1% per candle average)
    
    Returns:
        List of candlestick dictionaries
    """
    candles = []
    price = initial_price

    for i in range(num_candles):
        # Apply trend with some randomness
        price_change = price * trend * (0.5 + random.random())
        price += price_change

        # Generate OHLC
        open_price = price
        high = open_price * (1 + random.uniform(0, 0.02))
        low = open_price * (1 - random.uniform(0, 0.02))
        close = open_price + price_change
        volume = random.uniform(100, 1000)

        candles.append({
            'timestamp': i * 60,  # 1-minute candles
            'symbol': symbol,
            'open': round(open_price, 2),
            'high': round(high, 2),
            'low': round(low, 2),
            'close': round(close, 2),
            'volume': round(volume, 2)
        })

        price = close

    return candles


def generate_volatile_market(
        symbol: str = "BTC/USDT",
        initial_price: float = 50000.0,
        num_candles: int = 100,
        volatility: float = 0.05
) -> List[Dict[str, Any]]:
    """
    Generate a highly volatile market scenario.
    
    Args:
        symbol: Trading pair symbol
        initial_price: Starting price
        num_candles: Number of candlesticks to generate
        volatility: Volatility level (0.05 = 5% swings)
    
    Returns:
        List of candlestick dictionaries
    """
    candles = []
    price = initial_price

    for i in range(num_candles):
        # Large random swings
        price_change = price * volatility * random.uniform(-1, 1)

        open_price = price
        high = max(open_price, price + abs(price_change)) * (1 + random.uniform(0, volatility))
        low = min(open_price, price + price_change) * (1 - random.uniform(0, volatility))
        close = price + price_change
        volume = random.uniform(500, 2000)  # Higher volume during volatility

        candles.append({
            'timestamp': i * 60,
            'symbol': symbol,
            'open': round(open_price, 2),
            'high': round(high, 2),
            'low': round(low, 2),
            'close': round(close, 2),
            'volume': round(volume, 2)
        })

        price = close

    return candles


def generate_sideways_market(
        symbol: str = "BTC/USDT",
        initial_price: float = 50000.0,
        num_candles: int = 100,
        range_pct: float = 0.02
) -> List[Dict[str, Any]]:
    """
    Generate a sideways/ranging market scenario.
    
    Args:
        symbol: Trading pair symbol
        initial_price: Starting price
        num_candles: Number of candlesticks to generate
        range_pct: Price range as percentage (0.02 = ±2%)
    
    Returns:
        List of candlestick dictionaries
    """
    candles = []
    base_price = initial_price

    for i in range(num_candles):
        # Oscillate around base price
        price = base_price * (1 + range_pct * random.uniform(-1, 1))

        open_price = price
        high = open_price * (1 + random.uniform(0, range_pct / 2))
        low = open_price * (1 - random.uniform(0, range_pct / 2))
        close = base_price * (1 + range_pct * random.uniform(-1, 1))
        volume = random.uniform(100, 500)

        candles.append({
            'timestamp': i * 60,
            'symbol': symbol,
            'open': round(open_price, 2),
            'high': round(high, 2),
            'low': round(low, 2),
            'close': round(close, 2),
            'volume': round(volume, 2)
        })

    return candles


def generate_crash_scenario(
        symbol: str = "BTC/USDT",
        initial_price: float = 50000.0,
        crash_at: int = 50,
        num_candles: int = 100,
        crash_pct: float = 0.30
) -> List[Dict[str, Any]]:
    """
    Generate a market crash scenario.
    
    Args:
        symbol: Trading pair symbol
        initial_price: Starting price
        crash_at: Candle index where crash begins
        num_candles: Total number of candlesticks
        crash_pct: Crash magnitude (0.30 = 30% drop)
    
    Returns:
        List of candlestick dictionaries
    """
    candles = []
    price = initial_price

    for i in range(num_candles):
        if i < crash_at:
            # Normal market before crash
            price_change = price * 0.001 * random.uniform(-1, 1)
        elif i < crash_at + 10:
            # Crash phase - sharp drop
            price_change = -price * (crash_pct / 10) * random.uniform(0.8, 1.2)
        else:
            # Recovery phase
            price_change = price * 0.005 * random.uniform(0, 1)

        open_price = price
        close = price + price_change
        high = max(open_price, close) * (1 + random.uniform(0, 0.01))
        low = min(open_price, close) * (1 - random.uniform(0, 0.01))
        volume = random.uniform(100, 1000) * (5 if crash_at <= i < crash_at + 10 else 1)

        candles.append({
            'timestamp': i * 60,
            'symbol': symbol,
            'open': round(open_price, 2),
            'high': round(high, 2),
            'low': round(low, 2),
            'close': round(close, 2),
            'volume': round(volume, 2)
        })

        price = close

    return candles


# Prebuilt scenarios
SCENARIOS = {
    'bull_run': lambda: generate_trending_market(trend=0.01),
    'bear_market': lambda: generate_trending_market(trend=-0.01),
    'high_volatility': lambda: generate_volatile_market(volatility=0.05),
    'sideways': lambda: generate_sideways_market(range_pct=0.02),
    'flash_crash': lambda: generate_crash_scenario(crash_at=50, crash_pct=0.30),
}


def get_scenario(name: str) -> List[Dict[str, Any]]:
    """
    Get a predefined scenario by name.
    
    Args:
        name: Scenario name (bull_run, bear_market, high_volatility, sideways, flash_crash)
    
    Returns:
        List of candlestick dictionaries
    
    Raises:
        KeyError: If scenario name not found
    """
    if name not in SCENARIOS:
        raise KeyError(f"Scenario '{name}' not found. Available: {list(SCENARIOS.keys())}")

    return SCENARIOS[name]()


if __name__ == '__main__':
    # Demo: Generate and print a sample scenario
    print("🎰 Mock Exchange - Example Scenarios\n")

    for name in SCENARIOS:
        candles = get_scenario(name)
        print(f"📊 {name}:")
        print(f"   - Candles: {len(candles)}")
        print(f"   - Price range: ${candles[0]['close']:.2f} -> ${candles[-1]['close']:.2f}")
        print(f"   - Change: {((candles[-1]['close'] / candles[0]['close']) - 1) * 100:.2f}%")
        print()
