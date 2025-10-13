"""Candlestick pattern detection for trading analysis"""
from typing import Dict, Any
import pandas as pd


def _get_candle_body_size(candle: Dict[str, float]) -> float:
    """Calculate the size of the candle body"""
    return abs(candle['close'] - candle['open'])


def _get_candle_range(candle: Dict[str, float]) -> float:
    """Calculate the total range of the candle"""
    return candle['high'] - candle['low']


def _get_upper_wick(candle: Dict[str, float]) -> float:
    """Calculate the upper wick size"""
    return candle['high'] - max(candle['open'], candle['close'])


def _get_lower_wick(candle: Dict[str, float]) -> float:
    """Calculate the lower wick size"""
    return min(candle['open'], candle['close']) - candle['low']


def is_bullish(candle: Dict[str, float]) -> bool:
    """Check if candle is bullish (close > open)"""
    return candle['close'] > candle['open']


def is_bearish(candle: Dict[str, float]) -> bool:
    """Check if candle is bearish (close < open)"""
    return candle['close'] < candle['open']


def is_doji(candle: Dict[str, float], threshold: float = 0.1) -> bool:
    """Detect Doji pattern (open ≈ close)

    A Doji indicates indecision in the market.

    Args:
        candle: Dict with 'open', 'high', 'low', 'close'
        threshold: Max body size as % of total range (default: 0.1 = 10%)

    Returns:
        True if candle is a Doji
    """
    body_size = _get_candle_body_size(candle)
    total_range = _get_candle_range(candle)

    if total_range == 0:
        return True

    body_ratio = body_size / total_range
    return body_ratio <= threshold


def is_hammer(candle: Dict[str, float], wick_ratio: float = 1.5) -> bool:
    """Detect Hammer pattern (bullish reversal)

    A Hammer has a small body at the top and a long lower wick.
    Signals potential bullish reversal at bottom of downtrend.

    Args:
        candle: Dict with 'open', 'high', 'low', 'close'
        wick_ratio: Min ratio of lower wick to body (default: 1.5)

    Returns:
        True if candle is a Hammer
    """
    body_size = _get_candle_body_size(candle)
    lower_wick = _get_lower_wick(candle)
    upper_wick = _get_upper_wick(candle)
    total_range = _get_candle_range(candle)

    if total_range == 0:
        return False

    # Allow for doji-like hammers
    if body_size == 0:
        body_size = total_range * 0.05  # Use 5% of range as minimum body

    # Lower wick should be at least 1.5x the body
    # Upper wick should be small (less than body size)
    # Lower wick should be significant portion of total range
    return (
        lower_wick >= wick_ratio * body_size and
        upper_wick <= body_size and
        lower_wick >= total_range * 0.5  # Lower wick is at least 50% of total range
    )


def is_shooting_star(candle: Dict[str, float], wick_ratio: float = 1.5) -> bool:
    """Detect Shooting Star pattern (bearish reversal)

    A Shooting Star has a small body at the bottom and a long upper wick.
    Signals potential bearish reversal at top of uptrend.

    Args:
        candle: Dict with 'open', 'high', 'low', 'close'
        wick_ratio: Min ratio of upper wick to body (default: 1.5)

    Returns:
        True if candle is a Shooting Star
    """
    body_size = _get_candle_body_size(candle)
    lower_wick = _get_lower_wick(candle)
    upper_wick = _get_upper_wick(candle)
    total_range = _get_candle_range(candle)

    if total_range == 0:
        return False

    # Allow for doji-like shooting stars
    if body_size == 0:
        body_size = total_range * 0.05  # Use 5% of range as minimum body

    # Upper wick should be at least 1.5x the body
    # Lower wick should be small (less than body size)
    # Upper wick should be significant portion of total range
    return (
        upper_wick >= wick_ratio * body_size and
        lower_wick <= body_size and
        upper_wick >= total_range * 0.5  # Upper wick is at least 50% of total range
    )


def is_engulfing(candle1: Dict[str, float], candle2: Dict[str, float]) -> str:
    """Detect Engulfing pattern (reversal)

    Bullish Engulfing: Small bearish candle followed by larger bullish candle
    Bearish Engulfing: Small bullish candle followed by larger bearish candle

    Args:
        candle1: First candle (earlier)
        candle2: Second candle (later)

    Returns:
        'bullish_engulfing', 'bearish_engulfing', or 'none'
    """
    body1_size = _get_candle_body_size(candle1)
    body2_size = _get_candle_body_size(candle2)

    if body1_size == 0 or body2_size == 0:
        return 'none'

    # Bullish engulfing: bearish candle1, bullish candle2
    # candle2 body completely engulfs candle1 body
    if is_bearish(candle1) and is_bullish(candle2):
        if (candle2['open'] <= min(candle1['open'], candle1['close']) and
            candle2['close'] >= max(candle1['open'], candle1['close'])):
            return 'bullish_engulfing'

    # Bearish engulfing: bullish candle1, bearish candle2
    if is_bullish(candle1) and is_bearish(candle2):
        if (candle2['open'] >= max(candle1['open'], candle1['close']) and
            candle2['close'] <= min(candle1['open'], candle1['close'])):
            return 'bearish_engulfing'

    return 'none'


def is_morning_star(
    candle1: Dict[str, float],
    candle2: Dict[str, float],
    candle3: Dict[str, float]
) -> bool:
    """Detect Morning Star pattern (bullish reversal)

    Three-candle pattern:
    1. Large bearish candle
    2. Small-bodied candle (gap down)
    3. Large bullish candle (closes above midpoint of candle1)

    Args:
        candle1: First candle (bearish)
        candle2: Second candle (small body)
        candle3: Third candle (bullish)

    Returns:
        True if pattern is Morning Star
    """
    body1_size = _get_candle_body_size(candle1)
    body2_size = _get_candle_body_size(candle2)
    body3_size = _get_candle_body_size(candle3)

    if body1_size == 0 or body3_size == 0:
        return False

    # Candle 1 should be bearish
    if not is_bearish(candle1):
        return False

    # Candle 2 should have small body (< 0.3x candle1)
    if body2_size >= 0.3 * body1_size:
        return False

    # Candle 3 should be bullish
    if not is_bullish(candle3):
        return False

    # Candle 3 should close above midpoint of candle 1
    candle1_midpoint = (candle1['open'] + candle1['close']) / 2
    if candle3['close'] <= candle1_midpoint:
        return False

    return True


def is_evening_star(
    candle1: Dict[str, float],
    candle2: Dict[str, float],
    candle3: Dict[str, float]
) -> bool:
    """Detect Evening Star pattern (bearish reversal)

    Three-candle pattern:
    1. Large bullish candle
    2. Small-bodied candle (gap up)
    3. Large bearish candle (closes below midpoint of candle1)

    Args:
        candle1: First candle (bullish)
        candle2: Second candle (small body)
        candle3: Third candle (bearish)

    Returns:
        True if pattern is Evening Star
    """
    body1_size = _get_candle_body_size(candle1)
    body2_size = _get_candle_body_size(candle2)
    body3_size = _get_candle_body_size(candle3)

    if body1_size == 0 or body3_size == 0:
        return False

    # Candle 1 should be bullish
    if not is_bullish(candle1):
        return False

    # Candle 2 should have small body (< 0.3x candle1)
    if body2_size >= 0.3 * body1_size:
        return False

    # Candle 3 should be bearish
    if not is_bearish(candle3):
        return False

    # Candle 3 should close below midpoint of candle 1
    candle1_midpoint = (candle1['open'] + candle1['close']) / 2
    if candle3['close'] >= candle1_midpoint:
        return False

    return True


def scan_patterns(df: pd.DataFrame) -> Dict[str, Any]:
    """Scan DataFrame for all candlestick patterns

    Args:
        df: DataFrame with 'open', 'high', 'low', 'close' columns

    Returns:
        Dict with pattern names and list of indices where found
    """
    patterns = {
        'doji': [],
        'hammer': [],
        'shooting_star': [],
        'bullish_engulfing': [],
        'bearish_engulfing': [],
        'morning_star': [],
        'evening_star': []
    }

    # Single-candle patterns
    for i in range(len(df)):
        candle = df.iloc[i].to_dict()

        if is_doji(candle):
            patterns['doji'].append(i)
        if is_hammer(candle):
            patterns['hammer'].append(i)
        if is_shooting_star(candle):
            patterns['shooting_star'].append(i)

    # Two-candle patterns
    for i in range(1, len(df)):
        candle1 = df.iloc[i - 1].to_dict()
        candle2 = df.iloc[i].to_dict()

        engulfing = is_engulfing(candle1, candle2)
        if engulfing == 'bullish_engulfing':
            patterns['bullish_engulfing'].append(i)
        elif engulfing == 'bearish_engulfing':
            patterns['bearish_engulfing'].append(i)

    # Three-candle patterns
    for i in range(2, len(df)):
        candle1 = df.iloc[i - 2].to_dict()
        candle2 = df.iloc[i - 1].to_dict()
        candle3 = df.iloc[i].to_dict()

        if is_morning_star(candle1, candle2, candle3):
            patterns['morning_star'].append(i)
        if is_evening_star(candle1, candle2, candle3):
            patterns['evening_star'].append(i)

    return patterns
