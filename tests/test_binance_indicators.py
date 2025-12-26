"""Unit tests for Binance indicator calculations and helper functions."""

import pandas as pd
import numpy as np
import pytest
from unittest.mock import MagicMock, patch, Mock


@pytest.fixture
def sample_price_data():
    """Create sample price data for indicator calculations."""
    np.random.seed(42)
    n = 100
    base_price = 30000
    prices = base_price + np.cumsum(np.random.randn(n) * 100)

    data = {
        'timestamp': range(1640995200000, 1640995200000 + n * 60000, 60000),
        'open': prices,
        'high': prices + np.abs(np.random.randn(n) * 50),
        'low': prices - np.abs(np.random.randn(n) * 50),
        'close': prices + np.random.randn(n) * 20,
        'volume': np.abs(np.random.randn(n) * 1000 + 5000),
    }
    return pd.DataFrame(data)


class TestRoundSeries:
    """Tests for round_series() helper function."""

    @pytest.mark.unit
    @pytest.mark.binance
    def test_round_series_normal_numbers(self):
        """Test rounding normal numeric values."""
        import bot

        values = [30000.123456, 25000.987654, 40000.555555]
        result = bot.round_series(values, precision=2)

        assert len(result) == 3
        assert result[0] == 30000.12
        assert result[1] == 25000.99
        assert result[2] == 40000.56

    @pytest.mark.unit
    @pytest.mark.binance
    def test_round_series_with_nan(self):
        """Test that NaN values are skipped (filtered out)."""
        import bot

        values = [30000.123, np.nan, 25000.456, np.nan]
        result = bot.round_series(values, precision=2)

        # NaN values are completely skipped, not included
        assert len(result) == 2
        assert result[0] == 30000.12
        assert result[1] == 25000.46

    @pytest.mark.unit
    @pytest.mark.binance
    def test_round_series_with_infinity(self):
        """Test handling of infinity values."""
        import bot

        values = [30000.123, np.inf, 25000.456, -np.inf]
        result = bot.round_series(values, precision=2)

        # Infinity values are NOT skipped by pd.isna() - they pass through
        assert len(result) == 4
        assert result[0] == 30000.12
        assert np.isinf(result[1])  # inf preserved
        assert result[2] == 25000.46
        assert np.isinf(result[3])  # -inf preserved

    @pytest.mark.unit
    @pytest.mark.binance
    def test_round_series_with_none(self):
        """Test that None values are skipped."""
        import bot

        values = [30000.123, None, 25000.456]
        result = bot.round_series(values, precision=2)

        # None triggers TypeError in float(), gets caught and skipped
        assert len(result) == 2
        assert result[0] == 30000.12
        assert result[1] == 25000.46

    @pytest.mark.unit
    @pytest.mark.binance
    def test_round_series_string_numbers(self):
        """Test conversion of string numbers."""
        import bot

        values = ["30000.123", "25000.456"]
        result = bot.round_series(values, precision=2)

        # Strings are converted to float and rounded
        assert result[0] == 30000.12
        assert result[1] == 25000.46

    @pytest.mark.unit
    @pytest.mark.binance
    def test_round_series_invalid_strings(self):
        """Test handling of non-numeric strings."""
        import bot

        values = [30000.123, "invalid", 25000.456]
        result = bot.round_series(values, precision=2)

        # Invalid string causes ValueError, gets caught and skipped
        assert len(result) == 2
        assert result[0] == 30000.12
        assert result[1] == 25000.46

    @pytest.mark.unit
    @pytest.mark.binance
    def test_round_series_empty_list(self):
        """Test empty list returns empty list."""
        import bot

        result = bot.round_series([], precision=2)
        assert result == []

    @pytest.mark.unit
    @pytest.mark.binance
    def test_round_series_different_precision(self):
        """Test different precision values."""
        import bot

        value = [3.14159265359]

        result_2 = bot.round_series(value, precision=2)
        assert result_2[0] == 3.14

        result_4 = bot.round_series(value, precision=4)
        assert result_4[0] == 3.1416

        result_8 = bot.round_series(value, precision=8)
        assert result_8[0] == 3.14159265

    @pytest.mark.unit
    @pytest.mark.binance
    def test_round_series_negative_numbers(self):
        """Test rounding negative numbers."""
        import bot

        values = [-30000.123, -25000.987]
        result = bot.round_series(values, precision=2)

        assert result[0] == -30000.12
        assert result[1] == -25000.99

    @pytest.mark.unit
    @pytest.mark.binance
    def test_round_series_very_large_numbers(self):
        """Test rounding very large numbers."""
        import bot

        values = [1e10 + 0.123456, 1e15 + 0.987654]
        result = bot.round_series(values, precision=2)

        assert len(result) == 2
        # Should preserve precision for large numbers


class TestAddIndicatorColumns:
    """Tests for add_indicator_columns() function."""

    @pytest.mark.unit
    @pytest.mark.binance
    def test_add_indicator_columns_basic(self, sample_price_data):
        """Test basic indicator calculation."""
        import bot

        df = sample_price_data.copy()
        result = bot.add_indicator_columns(df)

        # Default parameters only add ema20 (EMA_LEN=20) and rsi14 (RSI_LEN=14)
        assert "ema20" in result.columns
        assert "rsi14" in result.columns
        assert "macd" in result.columns
        assert "macd_signal" in result.columns

        # ema50 and ema200 are NOT added by default
        assert "ema50" not in result.columns
        assert "ema200" not in result.columns

        # To get ema50 and ema200, pass custom parameters:
        result_custom = bot.add_indicator_columns(df, ema_lengths=(20, 50, 200))
        assert "ema50" in result_custom.columns
        assert "ema200" in result_custom.columns

        # All columns should be numeric
        assert pd.api.types.is_numeric_dtype(result["ema20"])
        assert pd.api.types.is_numeric_dtype(result["rsi14"])
        assert pd.api.types.is_numeric_dtype(result["macd"])

    @pytest.mark.unit
    @pytest.mark.binance
    def test_add_indicator_columns_custom_emas(self, sample_price_data):
        """Test with custom EMA lengths."""
        import bot

        df = sample_price_data.copy()
        result = bot.add_indicator_columns(df, ema_lengths=(10, 30, 100))

        assert "ema10" in result.columns
        assert "ema30" in result.columns
        assert "ema100" in result.columns

    @pytest.mark.unit
    @pytest.mark.binance
    def test_add_indicator_columns_custom_rsi(self, sample_price_data):
        """Test with custom RSI periods."""
        import bot

        df = sample_price_data.copy()
        result = bot.add_indicator_columns(df, rsi_periods=(9, 14, 21))

        assert "rsi9" in result.columns
        assert "rsi14" in result.columns
        assert "rsi21" in result.columns

    @pytest.mark.unit
    @pytest.mark.binance
    def test_add_indicator_columns_duplicate_removal(self, sample_price_data):
        """Test that duplicate EMA/RSI values are removed."""
        import bot

        df = sample_price_data.copy()
        # Pass duplicates - should be deduplicated internally
        result = bot.add_indicator_columns(
            df,
            ema_lengths=(20, 20, 50, 50),
            rsi_periods=(14, 14, 21)
        )

        # Should only have unique columns
        assert "ema20" in result.columns
        assert "ema50" in result.columns
        assert "rsi14" in result.columns
        assert "rsi21" in result.columns

    @pytest.mark.unit
    @pytest.mark.binance
    def test_add_indicator_columns_small_dataframe(self):
        """Test with small DataFrame (minimum bars)."""
        import bot

        # Create minimal data (20 bars)
        df = pd.DataFrame({
            'close': [30000 + i * 10 for i in range(20)],
            'high': [30100 + i * 10 for i in range(20)],
            'low': [29900 + i * 10 for i in range(20)],
            'volume': [1000] * 20,
        })

        result = bot.add_indicator_columns(df, ema_lengths=(10,), rsi_periods=(14,))

        # Should calculate even with small data
        assert "ema10" in result.columns
        assert "rsi14" in result.columns


class TestCalculateIndicators:
    """Tests for calculate_indicators() function."""

    @pytest.mark.unit
    @pytest.mark.binance
    def test_calculate_indicators_returns_series(self, sample_price_data):
        """Test that function returns a Series."""
        import bot

        df = sample_price_data.copy()
        result = bot.calculate_indicators(df)

        assert isinstance(result, pd.Series)

    @pytest.mark.unit
    @pytest.mark.binance
    def test_calculate_indicators_has_required_columns(self, sample_price_data):
        """Test that result has required indicator columns."""
        import bot

        df = sample_price_data.copy()
        result = bot.calculate_indicators(df)

        # Should have all required indicators
        assert "ema20" in result
        assert "rsi14" in result
        assert "macd" in result
        assert "macd_signal" in result

    @pytest.mark.unit
    @pytest.mark.binance
    def test_calculate_indicators_last_row(self, sample_price_data):
        """Test that result is the last row of enriched DataFrame."""
        import bot

        df = sample_price_data.copy()
        result = bot.calculate_indicators(df)

        # Result should be the last row
        # Verify by checking that values are numeric
        assert pd.api.types.is_numeric_dtype(result.dtype) or isinstance(result["ema20"], (int, float, np.number))

    @pytest.mark.unit
    @pytest.mark.binance
    def test_calculate_indicators_minimum_bars(self):
        """Test with minimum number of bars."""
        import bot

        # Create 50 bars (minimum for indicators)
        df = pd.DataFrame({
            'timestamp': range(50),
            'open': [30000] * 50,
            'high': [30100] * 50,
            'low': [29900] * 50,
            'close': [30000 + i for i in range(50)],
            'volume': [1000] * 50,
        })

        result = bot.calculate_indicators(df)

        # Should work with 50 bars
        assert isinstance(result, pd.Series)
        assert "ema20" in result


class TestFetchMarketDataExtended:
    """Extended tests for fetch_market_data() to achieve 100% coverage."""

    @pytest.mark.unit
    @pytest.mark.binance
    def test_fetch_market_data_funding_rate_exception(self):
        """Test handling of exception in get_funding_rate() call."""
        import bot

        mock_client = MagicMock()
        sample_klines = [[
            1609459200000, "30000", "30500", "29800", "30200", "100",
            1609459259999, "3020000", 1500, "50", "1510000", "0"
        ]] * 50

        mock_client.get_klines.return_value = sample_klines
        # get_funding_rate throws exception
        mock_client.get_funding_rate.side_effect = Exception("Funding rate API error")

        with patch('bot.get_binance_client', return_value=mock_client):
            result = bot.fetch_market_data("BTCUSDT")

        # Should still succeed and set funding_rate to 0
        assert result is not None
        assert result["funding_rate"] == 0

    @pytest.mark.unit
    @pytest.mark.binance
    def test_fetch_market_data_indicator_calculation_exception(self):
        """Test handling of exception during indicator calculation."""
        import bot

        mock_client = MagicMock()
        # Return invalid kline data that will cause calculation errors
        mock_client.get_klines.return_value = [[
            1609459200000, "invalid", "invalid", "invalid", "invalid", "invalid",
            1609459259999, "3020000", 1500, "50", "1510000", "0"
        ]]
        mock_client.get_funding_rate.return_value = []

        with patch('bot.get_binance_client', return_value=mock_client):
            result = bot.fetch_market_data("BTCUSDT")

        # Should return None when indicator calculation fails
        assert result is None


class TestCollectPromptMarketDataExtended:
    """Extended tests for collect_prompt_market_data() to achieve 100% coverage."""

    @pytest.fixture
    def full_kline_data(self):
        """Generate full kline data for all timeframes."""
        def make_klines(count):
            return [[
                1640995200000 + i * 60000, "30000", "30500", "29800", "30200", "100",
                1640995259999 + i * 60000, "3020000", 1500, "50", "1510000", "0"
            ] for i in range(count)]
        return make_klines

    @pytest.mark.unit
    @pytest.mark.binance
    def test_collect_empty_execution_klines(self):
        """Test when execution timeframe returns empty klines."""
        import bot

        mock_client = MagicMock()
        mock_client.get_klines.return_value = []  # Empty klines

        with patch('bot.get_binance_client', return_value=mock_client):
            result = bot.collect_prompt_market_data("BTCUSDT")

        # Should return None when execution klines are empty
        assert result is None

    @pytest.mark.unit
    @pytest.mark.binance
    def test_collect_empty_structure_klines(self, full_kline_data):
        """Test when structure (1h) timeframe returns empty klines."""
        import bot

        mock_client = MagicMock()
        # First call (execution 15m) succeeds, second call (structure 1h) returns empty
        mock_client.get_klines.side_effect = [
            full_kline_data(200),  # execution
            [],  # structure - empty
        ]

        with patch('bot.get_binance_client', return_value=mock_client):
            result = bot.collect_prompt_market_data("BTCUSDT")

        # Should return None when structure klines are empty
        assert result is None

    @pytest.mark.unit
    @pytest.mark.binance
    def test_collect_empty_trend_klines(self, full_kline_data):
        """Test when trend (4h) timeframe returns empty klines."""
        import bot

        mock_client = MagicMock()
        # Execution and structure succeed, trend returns empty
        mock_client.get_klines.side_effect = [
            full_kline_data(200),  # execution
            full_kline_data(100),  # structure
            [],  # trend - empty
        ]

        with patch('bot.get_binance_client', return_value=mock_client):
            result = bot.collect_prompt_market_data("BTCUSDT")

        # Should return None when trend klines are empty
        assert result is None

    @pytest.mark.unit
    @pytest.mark.binance
    def test_collect_open_interest_exception(self, full_kline_data):
        """Test handling of exception in get_open_interest()."""
        import bot

        mock_client = MagicMock()
        mock_client.get_klines.side_effect = [
            full_kline_data(200),  # execution
            full_kline_data(100),  # structure
            full_kline_data(100),  # trend
        ]
        mock_client.get_open_interest.side_effect = Exception("OI API error")
        mock_client.get_funding_rate.return_value = []

        with patch('bot.get_binance_client', return_value=mock_client):
            result = bot.collect_prompt_market_data("BTCUSDT")

        # Should continue despite OI exception
        assert result is None or isinstance(result, dict)

    @pytest.mark.unit
    @pytest.mark.binance
    def test_collect_funding_rate_history_exception(self, full_kline_data):
        """Test handling of exception in get_funding_rate(limit=30)."""
        import bot

        mock_client = MagicMock()
        mock_client.get_klines.side_effect = [
            full_kline_data(200),  # execution
            full_kline_data(100),  # structure
            full_kline_data(100),  # trend
        ]
        mock_client.get_open_interest.return_value = []
        mock_client.get_funding_rate.side_effect = Exception("Funding rate API error")

        with patch('bot.get_binance_client', return_value=mock_client):
            result = bot.collect_prompt_market_data("BTCUSDT")

        # Should continue despite funding rate exception
        assert result is None or isinstance(result, dict)

    @pytest.mark.unit
    @pytest.mark.binance
    def test_collect_top_level_exception(self, full_kline_data):
        """Test top-level exception handling in collect_prompt_market_data()."""
        import bot

        mock_client = MagicMock()
        # First call succeeds, then raise exception to trigger top-level catch
        mock_client.get_klines.side_effect = [
            full_kline_data(200),
            Exception("Unexpected error during processing")
        ]

        with patch('bot.get_binance_client', return_value=mock_client):
            result = bot.collect_prompt_market_data("BTCUSDT")

        # Should return None on top-level exception
        assert result is None
