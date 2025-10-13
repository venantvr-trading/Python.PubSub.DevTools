"""Tests for candlestick pattern detection with trading concepts"""
import pytest
from python_pubsub_devtools.trading.candle_patterns import (
    is_doji,
    is_hammer,
    is_shooting_star,
    is_engulfing,
    is_morning_star,
    is_evening_star,
    scan_patterns,
    is_bullish,
    is_bearish,
)
import pandas as pd


class TestBasicCandleProperties:
    """Test basic candle properties"""

    def test_bullish_candle(self):
        """Test bullish candle identification (close > open)"""
        candle = {'open': 50000, 'high': 51000, 'low': 49500, 'close': 50800}
        assert is_bullish(candle) is True
        assert is_bearish(candle) is False

    def test_bearish_candle(self):
        """Test bearish candle identification (close < open)"""
        candle = {'open': 50800, 'high': 51000, 'low': 49500, 'close': 50000}
        assert is_bearish(candle) is True
        assert is_bullish(candle) is False

    def test_neutral_candle(self):
        """Test neutral candle (close == open)"""
        candle = {'open': 50000, 'high': 50500, 'low': 49500, 'close': 50000}
        assert is_bullish(candle) is False
        assert is_bearish(candle) is False


class TestDojiPattern:
    """Test Doji pattern detection - indicates market indecision"""

    def test_perfect_doji(self):
        """Test perfect Doji (open == close)"""
        doji = {'open': 50000, 'high': 50500, 'low': 49500, 'close': 50000}
        assert is_doji(doji) is True

    def test_near_doji(self):
        """Test near-Doji (very small body, within threshold)"""
        near_doji = {'open': 50000, 'high': 50500, 'low': 49500, 'close': 50020}
        assert is_doji(near_doji, threshold=0.1) is True

    def test_not_doji(self):
        """Test non-Doji candle (large body)"""
        not_doji = {'open': 50000, 'high': 51000, 'low': 49500, 'close': 50800}
        assert is_doji(not_doji) is False

    def test_doji_in_btc_bull_run(self):
        """Test Doji during BTC bull run - signals potential pause"""
        # Realistic BTC prices during bull market
        doji_after_rally = {'open': 68000, 'high': 68200, 'low': 67800, 'close': 68010}
        assert is_doji(doji_after_rally, threshold=0.1) is True


class TestHammerPattern:
    """Test Hammer pattern - bullish reversal signal at bottom"""

    def test_perfect_hammer(self):
        """Test perfect Hammer (long lower wick, small body at top)"""
        hammer = {'open': 50000, 'high': 50100, 'low': 48000, 'close': 49900}
        assert is_hammer(hammer) is True

    def test_hammer_after_btc_crash(self):
        """Test Hammer after BTC crash - bullish reversal signal"""
        # Price drops to 42K, forms hammer, signals reversal
        hammer_reversal = {'open': 43000, 'high': 43200, 'low': 42000, 'close': 43100}
        assert is_hammer(hammer_reversal) is True

    def test_not_hammer_no_lower_wick(self):
        """Test non-Hammer (no significant lower wick)"""
        not_hammer = {'open': 50000, 'high': 51000, 'low': 49800, 'close': 50800}
        assert is_hammer(not_hammer) is False

    def test_inverted_hammer(self):
        """Test inverted Hammer (long upper wick) - should not be detected"""
        inverted = {'open': 50000, 'high': 52000, 'low': 49900, 'close': 50100}
        assert is_hammer(inverted) is False


class TestShootingStarPattern:
    """Test Shooting Star pattern - bearish reversal signal at top"""

    def test_perfect_shooting_star(self):
        """Test perfect Shooting Star (long upper wick, small body at bottom)"""
        shooting_star = {'open': 50000, 'high': 52000, 'low': 49900, 'close': 50100}
        assert is_shooting_star(shooting_star) is True

    def test_shooting_star_at_btc_ath(self):
        """Test Shooting Star at BTC all-time high - bearish signal"""
        # At 69K (ATH), long upper wick signals rejection
        ath_rejection = {'open': 68500, 'high': 69000, 'low': 68400, 'close': 68600}
        assert is_shooting_star(ath_rejection) is True

    def test_not_shooting_star(self):
        """Test non-Shooting Star (no upper wick)"""
        not_shooting_star = {'open': 50000, 'high': 50200, 'low': 48000, 'close': 49900}
        assert is_shooting_star(not_shooting_star) is False


class TestEngulfingPattern:
    """Test Engulfing patterns - strong reversal signals"""

    def test_bullish_engulfing(self):
        """Test Bullish Engulfing (bearish candle engulfed by bullish)"""
        bearish_candle = {'open': 50500, 'high': 50800, 'low': 50000, 'close': 50200}
        bullish_candle = {'open': 50000, 'high': 51000, 'low': 49800, 'close': 50900}

        result = is_engulfing(bearish_candle, bullish_candle)
        assert result == 'bullish_engulfing'

    def test_bearish_engulfing(self):
        """Test Bearish Engulfing (bullish candle engulfed by bearish)"""
        bullish_candle = {'open': 50000, 'high': 50800, 'low': 49800, 'close': 50500}
        bearish_candle = {'open': 50800, 'high': 51000, 'low': 49500, 'close': 49700}

        result = is_engulfing(bullish_candle, bearish_candle)
        assert result == 'bearish_engulfing'

    def test_bullish_engulfing_btc_bottom(self):
        """Test Bullish Engulfing at BTC bottom - strong buy signal"""
        # After capitulation, bullish engulfing signals bottom
        capitulation = {'open': 16000, 'high': 16200, 'low': 15500, 'close': 15600}
        reversal = {'open': 15400, 'high': 17000, 'low': 15300, 'close': 16800}

        result = is_engulfing(capitulation, reversal)
        assert result == 'bullish_engulfing'

    def test_no_engulfing(self):
        """Test non-engulfing pattern"""
        candle1 = {'open': 50000, 'high': 50500, 'low': 49500, 'close': 50200}
        candle2 = {'open': 50200, 'high': 50800, 'low': 50000, 'close': 50600}

        result = is_engulfing(candle1, candle2)
        assert result == 'none'


class TestMorningStarPattern:
    """Test Morning Star - strong bullish reversal (3-candle pattern)"""

    def test_perfect_morning_star(self):
        """Test perfect Morning Star pattern"""
        # Large bearish candle
        candle1 = {'open': 52000, 'high': 52200, 'low': 50000, 'close': 50200}
        # Small body (indecision)
        candle2 = {'open': 50000, 'high': 50200, 'low': 49800, 'close': 49900}
        # Large bullish candle
        candle3 = {'open': 50000, 'high': 52500, 'low': 49900, 'close': 52200}

        assert is_morning_star(candle1, candle2, candle3) is True

    def test_morning_star_btc_bear_market_bottom(self):
        """Test Morning Star at bear market bottom - signals trend reversal"""
        # Bear market bottom around 20K
        bear_candle = {'open': 22000, 'high': 22500, 'low': 19500, 'close': 20000}
        indecision = {'open': 19800, 'high': 20200, 'low': 19500, 'close': 19900}
        bull_reversal = {'open': 20000, 'high': 23000, 'low': 19800, 'close': 22500}

        assert is_morning_star(bear_candle, indecision, bull_reversal) is True

    def test_not_morning_star(self):
        """Test non-Morning Star pattern"""
        candle1 = {'open': 50000, 'high': 50500, 'low': 49500, 'close': 50200}
        candle2 = {'open': 50200, 'high': 50400, 'low': 50000, 'close': 50300}
        candle3 = {'open': 50300, 'high': 50800, 'low': 50100, 'close': 50600}

        assert is_morning_star(candle1, candle2, candle3) is False


class TestEveningStarPattern:
    """Test Evening Star - strong bearish reversal (3-candle pattern)"""

    def test_perfect_evening_star(self):
        """Test perfect Evening Star pattern"""
        # Large bullish candle
        candle1 = {'open': 50000, 'high': 52000, 'low': 49800, 'close': 51800}
        # Small body (indecision)
        candle2 = {'open': 52000, 'high': 52200, 'low': 51800, 'close': 52100}
        # Large bearish candle
        candle3 = {'open': 52000, 'high': 52200, 'low': 49500, 'close': 50000}

        assert is_evening_star(candle1, candle2, candle3) is True

    def test_evening_star_btc_top(self):
        """Test Evening Star at BTC local top - signals trend reversal"""
        # Local top around 65K
        rally_candle = {'open': 62000, 'high': 65000, 'low': 61800, 'close': 64500}
        exhaustion = {'open': 64800, 'high': 65200, 'low': 64500, 'close': 64900}
        reversal = {'open': 64700, 'high': 65000, 'low': 61000, 'close': 61500}

        assert is_evening_star(rally_candle, exhaustion, reversal) is True

    def test_not_evening_star(self):
        """Test non-Evening Star pattern"""
        candle1 = {'open': 50000, 'high': 50800, 'low': 49800, 'close': 50600}
        candle2 = {'open': 50600, 'high': 50900, 'low': 50400, 'close': 50700}
        candle3 = {'open': 50700, 'high': 51200, 'low': 50500, 'close': 51000}

        assert is_evening_star(candle1, candle2, candle3) is False


class TestPatternScanning:
    """Test pattern scanning on DataFrame (realistic trading scenario)"""

    def test_scan_bull_run_with_dojis(self):
        """Test scanning for patterns in bull run with consolidation Dojis"""
        # Simulate BTC bull run with occasional Dojis (consolidation)
        data = {
            'open': [50000, 51000, 51900, 52000, 52900, 53800],
            'high': [51200, 52000, 52100, 52200, 53100, 54000],
            'low': [49800, 50800, 51800, 51900, 52800, 53700],
            'close': [51000, 51900, 52000, 52950, 53800, 53900]
        }
        df = pd.DataFrame(data)

        patterns = scan_patterns(df)

        # Should detect Doji at index 2 (consolidation)
        assert 2 in patterns['doji']

    def test_scan_flash_crash_with_hammer(self):
        """Test scanning for Hammer after flash crash (reversal signal)"""
        # Simulate flash crash followed by hammer reversal
        data = {
            'open': [50000, 49000, 45000, 43000],
            'high': [50200, 49200, 45200, 43200],
            'low': [49000, 45000, 42000, 41000],  # Deep wick on candle 3
            'close': [49100, 45100, 42500, 43000]  # Recovery on candle 3
        }
        df = pd.DataFrame(data)

        patterns = scan_patterns(df)

        # Should detect Hammer at index 3 (bottom signal)
        assert 3 in patterns['hammer']

    def test_scan_pump_and_dump(self):
        """Test scanning pump and dump pattern (bullish then bearish engulfing)"""
        # Realistic pump and dump scenario
        data = {
            'open': [50000, 52000, 55000, 54000, 50000, 45000],
            'high': [52500, 55500, 56000, 55000, 54500, 50500],
            'low': [49800, 51800, 54800, 50000, 44500, 44000],
            'close': [52000, 55000, 54500, 50500, 45000, 44500]
        }
        df = pd.DataFrame(data)

        patterns = scan_patterns(df)

        # Should detect bearish engulfing during dump phase
        assert len(patterns['bearish_engulfing']) > 0

    def test_scan_multiple_patterns(self):
        """Test scanning for multiple pattern types in same dataset"""
        # Complex market with multiple patterns
        data = {
            'open': [50000, 50000, 51000, 52000, 51800, 51000, 50000],
            'high': [50500, 50200, 51500, 52500, 52000, 51200, 52000],
            'low': [49500, 49800, 50800, 51800, 49000, 50800, 49900],
            'close': [50000, 50100, 51400, 51900, 49500, 51100, 50100]
        }
        df = pd.DataFrame(data)

        patterns = scan_patterns(df)

        # Check that scan completed and returned all pattern types
        assert 'doji' in patterns
        assert 'hammer' in patterns
        assert 'shooting_star' in patterns
        assert 'bullish_engulfing' in patterns
        assert 'bearish_engulfing' in patterns


class TestRealisticTradingScenarios:
    """Test patterns in realistic trading scenarios"""

    def test_btc_2021_bull_market_exhaustion(self):
        """Test Evening Star at 2021 BTC top (realistic historical scenario)"""
        # Simulates BTC approaching 69K ATH with exhaustion
        rally = {'open': 66000, 'high': 68500, 'low': 65800, 'close': 68200}
        exhaustion = {'open': 68500, 'high': 69000, 'low': 68000, 'close': 68800}
        rejection = {'open': 68500, 'high': 69100, 'low': 64000, 'close': 65000}

        assert is_evening_star(rally, exhaustion, rejection) is True

    def test_eth_flash_crash_recovery(self):
        """Test Hammer during ETH flash crash (2021 scenario)"""
        # ETH flash crashed from 4000 to 1800, then recovered
        flash_crash = {'open': 2200, 'high': 2300, 'low': 1800, 'close': 2100}

        assert is_hammer(flash_crash) is True

    def test_altcoin_pump_detection(self):
        """Test detecting pump patterns in altcoin (typical pump & dump)"""
        # Typical altcoin pump: small body then huge engulfing
        before_pump = {'open': 0.50, 'high': 0.52, 'low': 0.49, 'close': 0.51}
        pump_candle = {'open': 0.52, 'high': 0.95, 'low': 0.51, 'close': 0.90}

        result = is_engulfing(before_pump, pump_candle)
        assert result == 'bullish_engulfing'

    def test_bear_market_capitulation(self):
        """Test Morning Star at bear market bottom (capitulation reversal)"""
        # Bear market capitulation around crypto winter lows
        capitulation = {'open': 18000, 'high': 18500, 'low': 15500, 'close': 16000}
        exhaustion = {'open': 15800, 'high': 16200, 'low': 15400, 'close': 15900}
        recovery = {'open': 16000, 'high': 19000, 'low': 15800, 'close': 18500}

        assert is_morning_star(capitulation, exhaustion, recovery) is True


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
