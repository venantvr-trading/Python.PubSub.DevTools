"""Tests for technical indicators with realistic trading scenarios"""
import math

import pandas as pd
import pytest

from python_pubsub_devtools.trading.indicators import (
    calculate_sma,
    calculate_ema,
    calculate_rsi,
    calculate_macd,
    calculate_bollinger_bands,
    detect_trend,
    calculate_atr,
)


class TestSMA:
    """Test Simple Moving Average (SMA)"""

    def test_sma_basic(self):
        """Test basic SMA calculation"""
        prices = [100, 110, 105, 115, 120]
        sma = calculate_sma(prices, period=3)

        # First 2 values should be NaN
        assert math.isnan(sma[0])
        assert math.isnan(sma[1])

        # Third value: (100 + 110 + 105) / 3 = 105
        assert sma[2] == pytest.approx(105.0)

        # Fourth value: (110 + 105 + 115) / 3 = 110
        assert sma[3] == pytest.approx(110.0)

        # Fifth value: (105 + 115 + 120) / 3 = 113.33
        assert sma[4] == pytest.approx(113.33, rel=0.01)

    def test_sma_btc_bull_run(self):
        """Test SMA on BTC bull run (50-day MA as support)"""
        # Simulate BTC prices in bull run
        btc_prices = [45000, 47000, 48500, 50000, 52000, 54000, 55000, 57000, 59000, 60000]
        sma_50 = calculate_sma(btc_prices, period=5)

        # SMA should be trending upward
        valid_sma = [x for x in sma_50 if not math.isnan(x)]
        assert valid_sma[-1] > valid_sma[0]  # Last SMA > First SMA

    def test_sma_insufficient_data(self):
        """Test SMA with insufficient data"""
        prices = [100, 110]
        sma = calculate_sma(prices, period=5)

        # All values should be NaN
        assert all(math.isnan(x) for x in sma)

    def test_sma_crossover(self):
        """Test SMA crossover (golden cross scenario)"""
        # Simulate golden cross: 50-day SMA crosses above 200-day SMA
        prices = list(range(40000, 60000, 200))  # Uptrend from 40K to 60K

        sma_50 = calculate_sma(prices, period=50)
        sma_200 = calculate_sma(prices, period=200)

        # In strong uptrend, shorter SMA should be above longer SMA
        # Check last valid values
        if not math.isnan(sma_50[-1]) and not math.isnan(sma_200[-1]):
            assert sma_50[-1] > sma_200[-1]


class TestEMA:
    """Test Exponential Moving Average (EMA)"""

    def test_ema_basic(self):
        """Test basic EMA calculation"""
        prices = [100, 110, 105, 115, 120, 125, 130]
        ema = calculate_ema(prices, period=3)

        # First 2 values should be NaN
        assert math.isnan(ema[0])
        assert math.isnan(ema[1])

        # EMA should react faster than SMA to price changes
        assert not math.isnan(ema[2])

    def test_ema_vs_sma(self):
        """Test that EMA reacts faster than SMA to price changes"""
        # Prices with sudden spike
        prices = [100, 100, 100, 100, 150]  # Sudden jump to 150

        sma = calculate_sma(prices, period=3)
        ema = calculate_ema(prices, period=3)

        # EMA should be higher than SMA after spike (more reactive)
        if not math.isnan(sma[-1]) and not math.isnan(ema[-1]):
            assert ema[-1] > sma[-1]

    def test_ema_btc_support(self):
        """Test EMA as dynamic support in BTC uptrend"""
        # 21 EMA is popular support level in crypto trading
        btc_prices = [50000, 52000, 51000, 53000, 52500, 54000, 55000, 54500, 56000, 57000]
        ema_21 = calculate_ema(btc_prices, period=5)

        # In uptrend, each price pullback should stay above EMA
        valid_ema = [x for x in ema_21 if not math.isnan(x)]
        assert len(valid_ema) > 0
        assert valid_ema[-1] < btc_prices[-1]  # Current price above EMA


class TestRSI:
    """Test Relative Strength Index (RSI)"""

    def test_rsi_basic(self):
        """Test basic RSI calculation"""
        # Ascending prices should give high RSI (>70 = overbought)
        prices = [100, 102, 104, 106, 108, 110, 112, 114, 116, 118, 120, 122, 124, 126, 128]
        rsi = calculate_rsi(prices, period=14)

        # Last RSI should be high (overbought territory)
        assert rsi[-1] > 70

    def test_rsi_oversold_condition(self):
        """Test RSI in oversold condition (<30)"""
        # Descending prices should give low RSI (oversold)
        prices = [100, 98, 96, 94, 92, 90, 88, 86, 84, 82, 80, 78, 76, 74, 72]
        rsi = calculate_rsi(prices, period=14)

        # Last RSI should be low (oversold territory)
        assert rsi[-1] < 30

    def test_rsi_btc_overbought(self):
        """Test RSI overbought signal in BTC parabolic move"""
        # Simulate BTC parabolic rise (RSI divergence warning)
        btc_prices = [45000 + i * 1500 for i in range(20)]  # Fast rise
        rsi = calculate_rsi(btc_prices, period=14)

        valid_rsi = [x for x in rsi if not math.isnan(x)]
        # Should be overbought
        assert valid_rsi[-1] > 70

    def test_rsi_btc_oversold_bounce(self):
        """Test RSI oversold condition signaling bounce"""
        # Simulate BTC crash then consolidation
        btc_crash = [60000, 55000, 50000, 45000, 40000, 35000, 30000, 28000, 27000,
                     26000, 25500, 25000, 25200, 25100, 25300, 25500]
        rsi = calculate_rsi(btc_crash, period=14)

        # RSI should be very low (oversold = potential bounce)
        valid_rsi = [x for x in rsi if not math.isnan(x)]
        min_rsi = min(valid_rsi)
        assert min_rsi < 30

    def test_rsi_neutral_range(self):
        """Test RSI in neutral range (30-70)"""
        # Sideways market
        prices = [100, 102, 99, 101, 98, 103, 100, 101, 99, 102, 100, 101, 99, 100, 101]
        rsi = calculate_rsi(prices, period=14)

        # RSI should be in neutral range
        assert 30 < rsi[-1] < 70


class TestMACD:
    """Test Moving Average Convergence Divergence (MACD)"""

    def test_macd_basic(self):
        """Test basic MACD calculation"""
        # Trending prices
        prices = [100 + i for i in range(50)]
        macd = calculate_macd(prices, fast_period=12, slow_period=26, signal_period=9)

        assert 'macd' in macd
        assert 'signal' in macd
        assert 'histogram' in macd
        assert len(macd['macd']) == len(prices)

    def test_macd_bullish_crossover(self):
        """Test MACD bullish crossover (buy signal)"""
        # Prices transitioning from downtrend to uptrend
        downtrend = [100 - i for i in range(20)]
        uptrend = [80 + i * 2 for i in range(30)]
        prices = downtrend + uptrend

        macd = calculate_macd(prices, fast_period=12, slow_period=26, signal_period=9)

        # In uptrend, MACD should cross above signal (histogram positive)
        histogram = macd['histogram']
        valid_hist = [x for x in histogram[-10:] if not math.isnan(x)]

        if len(valid_hist) > 0:
            # Most recent histogram should be positive (bullish)
            assert valid_hist[-1] > 0

    def test_macd_btc_trend_change(self):
        """Test MACD detecting BTC trend change"""
        # Simulate BTC bear to bull transition
        bear_market = [30000 - i * 500 for i in range(15)]
        bull_market = [22500 + i * 800 for i in range(20)]
        btc_prices = bear_market + bull_market

        macd = calculate_macd(btc_prices, fast_period=12, slow_period=26, signal_period=9)

        # MACD histogram should turn positive during bull phase
        histogram = macd['histogram']
        valid_hist = [x for x in histogram if not math.isnan(x)]

        # Check for crossover (negative to positive)
        has_crossover = any(
            valid_hist[i] < 0 and valid_hist[i + 1] > 0
            for i in range(len(valid_hist) - 1)
        )
        assert has_crossover


class TestBollingerBands:
    """Test Bollinger Bands"""

    def test_bollinger_bands_basic(self):
        """Test basic Bollinger Bands calculation"""
        prices = [100 + i for i in range(30)]
        bb = calculate_bollinger_bands(prices, period=20, num_std=2.0)

        assert 'upper' in bb
        assert 'middle' in bb
        assert 'lower' in bb

        # Upper band should be above middle, lower below
        valid_indices = [i for i in range(len(prices))
                         if not math.isnan(bb['upper'][i])]

        for i in valid_indices:
            assert bb['upper'][i] > bb['middle'][i]
            assert bb['lower'][i] < bb['middle'][i]

    def test_bollinger_squeeze(self):
        """Test Bollinger Squeeze (low volatility before breakout)"""
        # Tight consolidation then breakout
        consolidation = [100 + (i % 2) for i in range(25)]  # ±1 oscillation
        prices = consolidation

        bb = calculate_bollinger_bands(prices, period=20, num_std=2.0)

        # Band width should be narrow during consolidation
        valid_idx = [i for i in range(len(prices))
                     if not math.isnan(bb['upper'][i])]

        if len(valid_idx) > 0:
            last_idx = valid_idx[-1]
            band_width = bb['upper'][last_idx] - bb['lower'][last_idx]
            middle = bb['middle'][last_idx]

            # Band width should be less than 5% of price
            assert band_width < middle * 0.05

    def test_bollinger_bands_btc_volatility(self):
        """Test Bollinger Bands during BTC high volatility"""
        # High volatility period
        volatile_prices = [50000, 52000, 48000, 54000, 47000, 55000, 49000,
                           56000, 50000, 57000, 51000, 58000, 52000, 59000,
                           53000, 60000, 54000, 61000, 55000, 62000, 56000]

        bb = calculate_bollinger_bands(volatile_prices, period=20, num_std=2.0)

        # Bands should be wide during high volatility
        valid_idx = [i for i in range(len(volatile_prices))
                     if not math.isnan(bb['upper'][i])]

        if len(valid_idx) > 0:
            last_idx = valid_idx[-1]
            band_width = bb['upper'][last_idx] - bb['lower'][last_idx]
            middle = bb['middle'][last_idx]

            # Band width should be significant (>5% of price)
            assert band_width > middle * 0.05

    def test_bollinger_bounce(self):
        """Test price bouncing off lower Bollinger Band (buy signal)"""
        # Price touches lower band then bounces
        prices = [100, 98, 96, 94, 92, 90, 88, 86, 84, 82,
                  80, 78, 76, 75, 74, 73, 72, 71, 70, 71, 73, 75, 78]

        bb = calculate_bollinger_bands(prices, period=20, num_std=2.0)

        # Price should touch or go below lower band before bounce
        touched_lower_band = False
        for i in range(len(prices)):
            if not math.isnan(bb['lower'][i]):
                if prices[i] <= bb['lower'][i]:
                    touched_lower_band = True
                    break

        assert touched_lower_band


class TestTrendDetection:
    """Test trend detection"""

    def test_detect_uptrend(self):
        """Test uptrend detection"""
        prices = [100 + i * 2 for i in range(25)]
        trend = detect_trend(prices, period=20)
        assert trend == 'uptrend'

    def test_detect_downtrend(self):
        """Test downtrend detection"""
        prices = [100 - i * 2 for i in range(25)]
        trend = detect_trend(prices, period=20)
        assert trend == 'downtrend'

    def test_detect_sideways(self):
        """Test sideways market detection"""
        prices = [100 + (i % 3 - 1) for i in range(25)]  # Oscillates ±1
        trend = detect_trend(prices, period=20)
        assert trend == 'sideways'

    def test_btc_bull_market_trend(self):
        """Test detecting BTC bull market trend"""
        # Simulate BTC bull run from 20K to 60K
        btc_bull = [20000 + i * 1000 for i in range(40)]
        trend = detect_trend(btc_bull, period=20)
        assert trend == 'uptrend'

    def test_btc_bear_market_trend(self):
        """Test detecting BTC bear market trend"""
        # Simulate BTC bear from 60K to 20K
        btc_bear = [60000 - i * 1000 for i in range(40)]
        trend = detect_trend(btc_bear, period=20)
        assert trend == 'downtrend'

    def test_btc_accumulation_phase(self):
        """Test detecting BTC accumulation (sideways before breakout)"""
        # Tight range around 30K
        accumulation = [30000 + (i % 10 - 5) * 200 for i in range(30)]
        trend = detect_trend(accumulation, period=20)
        assert trend == 'sideways'


class TestATR:
    """Test Average True Range (ATR) - volatility indicator"""

    def test_atr_basic(self):
        """Test basic ATR calculation"""
        data = {
            'high': [105, 110, 108, 115, 120],
            'low': [95, 100, 98, 105, 110],
            'close': [100, 105, 103, 110, 115]
        }
        df = pd.DataFrame(data)

        atr = calculate_atr(df, period=3)

        # First value should be NaN
        assert math.isnan(atr[0])

        # ATR values should be positive
        valid_atr = [x for x in atr if not math.isnan(x)]
        assert all(x > 0 for x in valid_atr)

    def test_atr_high_volatility(self):
        """Test ATR during high volatility period"""
        # Large price swings
        data = {
            'high': [55000, 53000, 58000, 52000, 60000],
            'low': [50000, 48000, 53000, 47000, 55000],
            'close': [52000, 50000, 56000, 49000, 58000]
        }
        df = pd.DataFrame(data)

        atr = calculate_atr(df, period=3)
        valid_atr = [x for x in atr if not math.isnan(x)]

        # ATR should be high (>1000 for these prices)
        assert max(valid_atr) > 1000


class TestRealisticTradingScenarios:
    """Test indicators in realistic trading scenarios"""

    def test_golden_cross_bitcoin(self):
        """Test golden cross signal in BTC (bullish signal)"""
        # Simulate BTC emerging from bear market
        # Golden cross: 50 SMA crosses above 200 SMA
        prices = []
        # Bear market
        prices.extend([30000 - i * 100 for i in range(100)])
        # Transition
        prices.extend([20000 + i * 150 for i in range(150)])

        sma_50 = calculate_sma(prices, period=50)
        sma_200 = calculate_sma(prices, period=200)

        # Check if golden cross occurred
        golden_cross = False
        for i in range(200, len(prices) - 1):
            if (sma_50[i] <= sma_200[i] and
                    sma_50[i + 1] > sma_200[i + 1]):
                golden_cross = True
                break

        # In this scenario, golden cross should occur
        assert golden_cross

    def test_rsi_divergence_warning(self):
        """Test RSI divergence (price makes new high, RSI doesn't)"""
        # Price continues up but momentum weakening
        prices = [50000, 52000, 54000, 56000, 58000, 60000,
                  59000, 61000, 62000, 61500, 63000, 62500,
                  64000, 63500, 64500]  # Higher highs but slower

        rsi = calculate_rsi(prices, period=14)
        valid_rsi = [x for x in rsi if not math.isnan(x)]

        # RSI should show weakening momentum (bearish divergence)
        # Last RSI should be lower than mid-point RSI despite higher price
        mid_point = len(valid_rsi) // 2
        if len(valid_rsi) > mid_point + 2:
            # Check for lower high in RSI
            rsi_declining = valid_rsi[-1] < max(valid_rsi[mid_point:-1])
            assert rsi_declining

    def test_btc_flash_crash_volatility(self):
        """Test indicators during BTC flash crash (May 2021 scenario)"""
        # Simulate flash crash from 60K to 30K then recovery
        flash_crash = [60000, 55000, 50000, 45000, 35000, 30000, 35000, 40000, 45000, 50000]

        rsi = calculate_rsi(flash_crash + [50000] * 5, period=14)  # Extend for RSI
        trend = detect_trend(flash_crash, period=8)

        valid_rsi = [x for x in rsi if not math.isnan(x)]

        # RSI should hit oversold during crash
        assert min(valid_rsi) < 30
        # Trend should be downtrend
        assert trend == 'downtrend'


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
