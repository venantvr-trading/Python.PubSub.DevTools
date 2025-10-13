"""Technical indicators for trading analysis"""
import math
from typing import List, Dict

import pandas as pd


def calculate_sma(prices: List[float], period: int) -> List[float]:
    """Calculate Simple Moving Average (SMA)

    Args:
        prices: List of prices
        period: Period for the moving average

    Returns:
        List of SMA values (NaN for insufficient data)
    """
    if len(prices) < period:
        return [float('nan')] * len(prices)

    sma = []
    for i in range(len(prices)):
        if i < period - 1:
            sma.append(float('nan'))
        else:
            window = prices[i - period + 1:i + 1]
            sma.append(sum(window) / period)

    return sma


def calculate_ema(prices: List[float], period: int) -> List[float]:
    """Calculate Exponential Moving Average (EMA)

    Args:
        prices: List of prices
        period: Period for the moving average

    Returns:
        List of EMA values
    """
    if len(prices) < period:
        return [float('nan')] * len(prices)

    multiplier = 2 / (period + 1)
    ema = []

    # Start with SMA for first value
    sma_start = sum(prices[:period]) / period
    ema.append(sma_start)

    # Calculate EMA for remaining values
    for i in range(1, len(prices)):
        if i < period - 1:
            ema.insert(0, float('nan'))
        else:
            ema_value = (prices[i] - ema[-1]) * multiplier + ema[-1]
            ema.append(ema_value)

    # Pad beginning with NaN
    while len(ema) < len(prices):
        ema.insert(0, float('nan'))

    return ema


def calculate_rsi(prices: List[float], period: int = 14) -> List[float]:
    """Calculate Relative Strength Index (RSI)

    Args:
        prices: List of prices
        period: RSI period (default: 14)

    Returns:
        List of RSI values (0-100)
    """
    if len(prices) < period + 1:
        return [float('nan')] * len(prices)

    # Calculate price changes
    changes = [prices[i] - prices[i - 1] for i in range(1, len(prices))]

    # Separate gains and losses
    gains = [max(change, 0) for change in changes]
    losses = [abs(min(change, 0)) for change in changes]

    rsi = [float('nan')]  # First value is always NaN

    # Calculate initial average gain/loss
    avg_gain = sum(gains[:period]) / period
    avg_loss = sum(losses[:period]) / period

    # Calculate first RSI
    if avg_loss == 0:
        rsi.append(100.0)
    else:
        rs = avg_gain / avg_loss
        rsi.append(100 - (100 / (1 + rs)))

    # Calculate remaining RSI values using smoothed averages
    for i in range(period, len(changes)):
        avg_gain = ((avg_gain * (period - 1)) + gains[i]) / period
        avg_loss = ((avg_loss * (period - 1)) + losses[i]) / period

        if avg_loss == 0:
            rsi.append(100.0)
        else:
            rs = avg_gain / avg_loss
            rsi.append(100 - (100 / (1 + rs)))

    # Pad beginning with NaN
    while len(rsi) < len(prices):
        rsi.insert(0, float('nan'))

    return rsi


def calculate_macd(
        prices: List[float],
        fast_period: int = 12,
        slow_period: int = 26,
        signal_period: int = 9
) -> Dict[str, List[float]]:
    """Calculate MACD (Moving Average Convergence Divergence)

    Args:
        prices: List of prices
        fast_period: Fast EMA period (default: 12)
        slow_period: Slow EMA period (default: 26)
        signal_period: Signal line period (default: 9)

    Returns:
        Dict with 'macd', 'signal', and 'histogram' lists
    """
    fast_ema = calculate_ema(prices, fast_period)
    slow_ema = calculate_ema(prices, slow_period)

    # Calculate MACD line
    macd_line = []
    for fast, slow in zip(fast_ema, slow_ema):
        if math.isnan(fast) or math.isnan(slow):
            macd_line.append(float('nan'))
        else:
            macd_line.append(fast - slow)

    # Calculate signal line (EMA of MACD)
    # Remove NaN values for signal calculation
    valid_macd = [x for x in macd_line if not math.isnan(x)]
    if len(valid_macd) >= signal_period:
        signal_line = calculate_ema(valid_macd, signal_period)
        # Pad signal line to match length
        nan_count = len(macd_line) - len(signal_line)
        signal_line = [float('nan')] * nan_count + signal_line
    else:
        signal_line = [float('nan')] * len(macd_line)

    # Calculate histogram
    histogram = []
    for macd, signal in zip(macd_line, signal_line):
        if math.isnan(macd) or math.isnan(signal):
            histogram.append(float('nan'))
        else:
            histogram.append(macd - signal)

    return {
        'macd': macd_line,
        'signal': signal_line,
        'histogram': histogram
    }


def calculate_bollinger_bands(
        prices: List[float],
        period: int = 20,
        num_std: float = 2.0
) -> Dict[str, List[float]]:
    """Calculate Bollinger Bands

    Args:
        prices: List of prices
        period: Period for moving average (default: 20)
        num_std: Number of standard deviations (default: 2.0)

    Returns:
        Dict with 'upper', 'middle', and 'lower' band lists
    """
    middle = calculate_sma(prices, period)

    upper = []
    lower = []

    for i in range(len(prices)):
        if i < period - 1 or math.isnan(middle[i]):
            upper.append(float('nan'))
            lower.append(float('nan'))
        else:
            # Calculate standard deviation for window
            window = prices[i - period + 1:i + 1]
            mean = sum(window) / period
            variance = sum((x - mean) ** 2 for x in window) / period
            std_dev = math.sqrt(variance)

            upper.append(middle[i] + (num_std * std_dev))
            lower.append(middle[i] - (num_std * std_dev))

    return {
        'upper': upper,
        'middle': middle,
        'lower': lower
    }


def detect_trend(prices: List[float], period: int = 20) -> str:
    """Detect market trend based on price movement

    Args:
        prices: List of prices
        period: Period to analyze

    Returns:
        'uptrend', 'downtrend', or 'sideways'
    """
    if len(prices) < period:
        return 'insufficient_data'

    recent_prices = prices[-period:]

    # Calculate linear regression slope
    n = len(recent_prices)
    x_mean = (n - 1) / 2
    y_mean = sum(recent_prices) / n

    numerator = sum((i - x_mean) * (recent_prices[i] - y_mean) for i in range(n))
    denominator = sum((i - x_mean) ** 2 for i in range(n))

    if denominator == 0:
        return 'sideways'

    slope = numerator / denominator

    # Determine trend based on slope
    # Threshold is 0.1% per candle
    threshold = y_mean * 0.001

    if slope > threshold:
        return 'uptrend'
    elif slope < -threshold:
        return 'downtrend'
    else:
        return 'sideways'


def calculate_atr(df: pd.DataFrame, period: int = 14) -> List[float]:
    """Calculate Average True Range (ATR)

    Args:
        df: DataFrame with 'high', 'low', 'close' columns
        period: ATR period (default: 14)

    Returns:
        List of ATR values
    """
    if len(df) < 2:
        return [float('nan')] * len(df)

    true_ranges = [float('nan')]  # First TR is undefined

    for i in range(1, len(df)):
        high = df.iloc[i]['high']
        low = df.iloc[i]['low']
        prev_close = df.iloc[i - 1]['close']

        tr = max(
            high - low,
            abs(high - prev_close),
            abs(low - prev_close)
        )
        true_ranges.append(tr)

    # Calculate ATR using exponential moving average
    atr = []
    for i in range(len(true_ranges)):
        if i < period or math.isnan(true_ranges[i]):
            atr.append(float('nan'))
        elif i == period:
            # First ATR is simple average
            atr.append(sum(true_ranges[1:period + 1]) / period)
        else:
            # Subsequent ATRs use exponential smoothing
            prev_atr = atr[-1]
            atr.append((prev_atr * (period - 1) + true_ranges[i]) / period)

    return atr
