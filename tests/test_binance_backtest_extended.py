"""Extended unit tests for Binance backtest functionality to achieve 100% coverage."""

import os
import pandas as pd
import numpy as np
import pytest
from pathlib import Path
from unittest.mock import MagicMock, patch, Mock
from datetime import datetime, timedelta
import tempfile
import shutil


@pytest.fixture
def temp_cache_dir():
    """Create a temporary cache directory for tests."""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    shutil.rmtree(temp_dir, ignore_errors=True)


@pytest.fixture
def sample_backtest_config():
    """Create a sample backtest configuration."""
    from backtest import BacktestConfig

    return BacktestConfig(
        start=datetime(2022, 1, 1, 0, 0, 0),
        end=datetime(2022, 1, 7, 0, 0, 0),
        interval="15m",
        base_dir=Path("data-backtest"),
        run_dir=Path("data-backtest/run-test"),
        cache_dir=Path("data-backtest/cache"),
        run_id="test-run",
        model=None,
        temperature=None,
        max_tokens=None,
        thinking=None,
        system_prompt=None,
        system_prompt_file=None,
        start_capital=10000.0,
        disable_telegram=True
    )


@pytest.fixture
def generate_klines():
    """Factory fixture to generate kline data."""
    def _generate(start_ts=1640995200000, count=100, interval_ms=900000):
        return [[
            start_ts + i * interval_ms,  # timestamp
            f"{30000 + i * 10}",  # open
            f"{30500 + i * 10}",  # high
            f"{29800 + i * 10}",  # low
            f"{30200 + i * 10}",  # close
            f"{100 + i}",  # volume
            start_ts + i * interval_ms + interval_ms - 1,  # close_time
            f"{3020000 + i * 1000}",  # quote_volume
            1500 + i,  # trades
            f"{50 + i}",  # taker_base
            f"{1510000 + i * 100}",  # taker_quote
            "0"  # ignore
        ] for i in range(count)]
    return _generate


class TestNormalizeKlineDataframeExtended:
    """Extended tests for normalize_kline_dataframe() to achieve 100% coverage."""

    @pytest.mark.unit
    @pytest.mark.binance
    def test_normalize_all_close_time_nan(self):
        """Test when all close_time values are NaN."""
        import backtest

        data = [
            [1640995200000, "46000", "46500", "45800", "46200", "100",
             None, "4632000", 1500, "50", "2316000", "0"],  # close_time is None
            [1640995260000, "46200", "46800", "46100", "46600", "120",
             None, "5606000", 1800, "60", "2803000", "0"],
        ]

        df = pd.DataFrame(data, columns=backtest.KLINE_COLUMNS)
        normalized = backtest.normalize_kline_dataframe(df)

        # close_time should be filled with timestamp values
        assert (normalized["close_time"] == normalized["timestamp"]).all()

    @pytest.mark.unit
    @pytest.mark.binance
    def test_normalize_all_trades_nan(self):
        """Test when all trades values are NaN."""
        import backtest

        data = [
            [1640995200000, "46000", "46500", "45800", "46200", "100",
             1640995259999, "4632000", None, "50", "2316000", "0"],  # trades is None
            [1640995260000, "46200", "46800", "46100", "46600", "120",
             1640995319999, "5606000", None, "60", "2803000", "0"],
        ]

        df = pd.DataFrame(data, columns=backtest.KLINE_COLUMNS)
        normalized = backtest.normalize_kline_dataframe(df)

        # trades should be filled with 0
        assert (normalized["trades"] == 0).all()

    @pytest.mark.unit
    @pytest.mark.binance
    def test_normalize_timestamp_with_nan(self):
        """Test that rows with NaN timestamp are dropped."""
        import backtest

        data = [
            [1640995200000, "46000", "46500", "45800", "46200", "100",
             1640995259999, "4632000", 1500, "50", "2316000", "0"],
            [None, "46200", "46800", "46100", "46600", "120",  # NaN timestamp
             1640995319999, "5606000", 1800, "60", "2803000", "0"],
            [1640995320000, "46600", "47000", "46400", "46800", "150",
             1640995379999, "7052000", 2100, "75", "3526000", "0"],
        ]

        df = pd.DataFrame(data, columns=backtest.KLINE_COLUMNS)
        normalized = backtest.normalize_kline_dataframe(df)

        # Should drop the row with NaN timestamp
        assert len(normalized) == 2
        assert normalized.iloc[0]["timestamp"] == 1640995200000
        assert normalized.iloc[1]["timestamp"] == 1640995320000

    @pytest.mark.unit
    @pytest.mark.binance
    def test_normalize_completely_empty_dataframe(self):
        """Test with completely empty DataFrame."""
        import backtest

        df = pd.DataFrame(columns=backtest.KLINE_COLUMNS)
        normalized = backtest.normalize_kline_dataframe(df)

        assert normalized.empty
        assert list(normalized.columns) == backtest.KLINE_COLUMNS

    @pytest.mark.unit
    @pytest.mark.binance
    def test_normalize_single_row(self):
        """Test with single row DataFrame."""
        import backtest

        data = [[1640995200000, "46000", "46500", "45800", "46200", "100",
                 1640995259999, "4632000", 1500, "50", "2316000", "0"]]

        df = pd.DataFrame(data, columns=backtest.KLINE_COLUMNS)
        normalized = backtest.normalize_kline_dataframe(df)

        assert len(normalized) == 1
        assert normalized.iloc[0]["close"] == 46200.0

    @pytest.mark.unit
    @pytest.mark.binance
    def test_normalize_negative_prices(self):
        """Test that negative prices (invalid but should be preserved)."""
        import backtest

        data = [[1640995200000, "-46000", "-46500", "-45800", "-46200", "100",
                 1640995259999, "4632000", 1500, "50", "2316000", "0"]]

        df = pd.DataFrame(data, columns=backtest.KLINE_COLUMNS)
        normalized = backtest.normalize_kline_dataframe(df)

        # Negative values should be preserved (as-is)
        assert normalized.iloc[0]["open"] == -46000.0

    @pytest.mark.unit
    @pytest.mark.binance
    def test_normalize_very_large_numbers(self):
        """Test with very large numbers (precision edge case)."""
        import backtest

        data = [[1640995200000, "1e15", "1e15", "1e15", "1e15", "1e10",
                 1640995259999, "1e18", 1500, "1e8", "1e12", "0"]]

        df = pd.DataFrame(data, columns=backtest.KLINE_COLUMNS)
        normalized = backtest.normalize_kline_dataframe(df)

        assert normalized.iloc[0]["open"] == 1e15


class TestEnsureCachedKlinesExtended:
    """Extended tests for ensure_cached_klines() to achieve 100% coverage."""

    @pytest.mark.unit
    @pytest.mark.binance
    def test_cache_hit_full_coverage(self, sample_backtest_config, temp_cache_dir, generate_klines):
        """Test cache HIT scenario - data already cached and covers full range."""
        import backtest

        sample_backtest_config.cache_dir = Path(temp_cache_dir)
        cache_file = Path(temp_cache_dir) / "BTCUSDT_15m.csv"
        cache_file.parent.mkdir(parents=True, exist_ok=True)

        # Calculate required start time INCLUDING warmup buffer
        # For 15m, warmup is 200 bars = 200 * 15 minutes = 3000 minutes
        warmup = backtest.WARMUP_BARS.get("15m", 0)  # 200 bars
        interval_delta = backtest.interval_to_timedelta("15m")
        start_with_buffer = sample_backtest_config.start - interval_delta * warmup

        # Create cached data that starts BEFORE the buffered start time
        # and ends AFTER the config end time
        cache_start_ms = int(start_with_buffer.timestamp() * 1000) - 900000 * 50  # 50 extra bars before
        cache_end_ms = int(sample_backtest_config.end.timestamp() * 1000) + 900000 * 50  # 50 extra bars after

        # Generate enough klines to cover the full range
        total_bars = int((cache_end_ms - cache_start_ms) / 900000) + 1
        cached_klines = generate_klines(start_ts=cache_start_ms, count=total_bars, interval_ms=900000)
        df_cache = pd.DataFrame(cached_klines, columns=backtest.KLINE_COLUMNS)
        df_cache = backtest.normalize_kline_dataframe(df_cache)
        df_cache.to_csv(cache_file, index=False)

        mock_client = MagicMock()

        # Call ensure_cached_klines
        result = backtest.ensure_cached_klines(
            mock_client,
            sample_backtest_config,
            "BTCUSDT",
            "15m"
        )

        # Should NOT call get_historical_klines (cache hit)
        mock_client.get_historical_klines.assert_not_called()

        # Should return data
        assert isinstance(result, pd.DataFrame)
        assert len(result) > 0

    @pytest.mark.unit
    @pytest.mark.binance
    def test_cache_miss_fetch_from_binance(self, sample_backtest_config, temp_cache_dir, generate_klines):
        """Test cache MISS - no cache file, fetch from Binance."""
        import backtest

        sample_backtest_config.cache_dir = Path(temp_cache_dir)
        Path(temp_cache_dir).mkdir(parents=True, exist_ok=True)

        mock_client = MagicMock()
        mock_client.get_historical_klines.return_value = generate_klines(count=200)

        result = backtest.ensure_cached_klines(
            mock_client,
            sample_backtest_config,
            "BTCUSDT",
            "15m"
        )

        # Should call Binance API
        mock_client.get_historical_klines.assert_called_once()

        # Should return DataFrame
        assert isinstance(result, pd.DataFrame)
        assert len(result) > 0

    @pytest.mark.unit
    @pytest.mark.binance
    def test_cache_partial_coverage_merge(self, sample_backtest_config, temp_cache_dir, generate_klines):
        """Test partial cache coverage - merges cached + fresh data."""
        import backtest

        sample_backtest_config.cache_dir = Path(temp_cache_dir)
        cache_file = Path(temp_cache_dir) / "BTCUSDT_15m.csv"
        cache_file.parent.mkdir(parents=True, exist_ok=True)

        # Cache only covers PART of the range (first 100 bars)
        start_ms = int(sample_backtest_config.start.timestamp() * 1000)
        cached_klines = generate_klines(start_ts=start_ms, count=100, interval_ms=900000)
        df_cache = pd.DataFrame(cached_klines, columns=backtest.KLINE_COLUMNS)
        df_cache = backtest.normalize_kline_dataframe(df_cache)
        df_cache.to_csv(cache_file, index=False)

        mock_client = MagicMock()
        # Return fresh data for the rest
        fresh_klines = generate_klines(start_ts=start_ms + 100 * 900000, count=600, interval_ms=900000)
        mock_client.get_historical_klines.return_value = fresh_klines

        result = backtest.ensure_cached_klines(
            mock_client,
            sample_backtest_config,
            "BTCUSDT",
            "15m"
        )

        # Should call Binance API to fetch missing data
        mock_client.get_historical_klines.assert_called_once()

        # Should merge and return combined data
        assert isinstance(result, pd.DataFrame)
        assert len(result) > 100  # More than just cache

    @pytest.mark.unit
    @pytest.mark.binance
    def test_cache_write_to_disk(self, sample_backtest_config, temp_cache_dir, generate_klines):
        """Test that cache is written to disk after fetching."""
        import backtest

        sample_backtest_config.cache_dir = Path(temp_cache_dir)
        Path(temp_cache_dir).mkdir(parents=True, exist_ok=True)
        cache_file = Path(temp_cache_dir) / "BTCUSDT_15m.csv"

        mock_client = MagicMock()
        mock_client.get_historical_klines.return_value = generate_klines(count=200)

        backtest.ensure_cached_klines(
            mock_client,
            sample_backtest_config,
            "BTCUSDT",
            "15m"
        )

        # Cache file should be created
        assert cache_file.exists()

        # Cache file should have valid data
        cached_df = pd.read_csv(cache_file)
        assert len(cached_df) > 0

    @pytest.mark.unit
    @pytest.mark.binance
    def test_cache_deduplication(self, sample_backtest_config, temp_cache_dir, generate_klines):
        """Test that duplicate timestamps are deduplicated during merge."""
        import backtest

        sample_backtest_config.cache_dir = Path(temp_cache_dir)
        cache_file = Path(temp_cache_dir) / "BTCUSDT_15m.csv"
        cache_file.parent.mkdir(parents=True, exist_ok=True)

        # Create cached data with some duplicates
        start_ms = int(sample_backtest_config.start.timestamp() * 1000)
        cached_klines = generate_klines(start_ts=start_ms, count=100, interval_ms=900000)
        df_cache = pd.DataFrame(cached_klines, columns=backtest.KLINE_COLUMNS)
        df_cache = backtest.normalize_kline_dataframe(df_cache)
        df_cache.to_csv(cache_file, index=False)

        mock_client = MagicMock()
        # Fresh data overlaps with cached (some duplicate timestamps)
        fresh_klines = generate_klines(start_ts=start_ms + 50 * 900000, count=600, interval_ms=900000)
        mock_client.get_historical_klines.return_value = fresh_klines

        result = backtest.ensure_cached_klines(
            mock_client,
            sample_backtest_config,
            "BTCUSDT",
            "15m"
        )

        # Should deduplicate - no duplicate timestamps
        assert result["timestamp"].is_unique

    @pytest.mark.unit
    @pytest.mark.binance
    def test_cache_different_symbols_no_interference(self, sample_backtest_config, temp_cache_dir, generate_klines):
        """Test that different symbols use separate cache files."""
        import backtest

        sample_backtest_config.cache_dir = Path(temp_cache_dir)
        Path(temp_cache_dir).mkdir(parents=True, exist_ok=True)

        mock_client = MagicMock()
        mock_client.get_historical_klines.return_value = generate_klines(count=200)

        # Fetch for BTC
        backtest.ensure_cached_klines(mock_client, sample_backtest_config, "BTCUSDT", "15m")

        # Fetch for ETH
        backtest.ensure_cached_klines(mock_client, sample_backtest_config, "ETHUSDT", "15m")

        # Should have separate cache files
        btc_cache = Path(temp_cache_dir) / "BTCUSDT_15m.csv"
        eth_cache = Path(temp_cache_dir) / "ETHUSDT_15m.csv"

        assert btc_cache.exists()
        assert eth_cache.exists()
        assert btc_cache != eth_cache

    @pytest.mark.unit
    @pytest.mark.binance
    def test_cache_different_intervals(self, sample_backtest_config, temp_cache_dir, generate_klines):
        """Test that different intervals use separate cache files."""
        import backtest

        sample_backtest_config.cache_dir = Path(temp_cache_dir)
        Path(temp_cache_dir).mkdir(parents=True, exist_ok=True)

        mock_client = MagicMock()
        mock_client.get_historical_klines.return_value = generate_klines(count=200)

        # Fetch 15m
        backtest.ensure_cached_klines(mock_client, sample_backtest_config, "BTCUSDT", "15m")

        # Fetch 1h
        backtest.ensure_cached_klines(mock_client, sample_backtest_config, "BTCUSDT", "1h")

        # Should have separate cache files
        cache_15m = Path(temp_cache_dir) / "BTCUSDT_15m.csv"
        cache_1h = Path(temp_cache_dir) / "BTCUSDT_1h.csv"

        assert cache_15m.exists()
        assert cache_1h.exists()


class TestHistoricalBinanceClientExtended:
    """Extended tests for HistoricalBinanceClient to achieve 100% coverage."""

    @pytest.fixture
    def setup_client_with_data(self, generate_klines):
        """Create client with realistic data."""
        import backtest

        klines_15m = generate_klines(start_ts=1640995200000, count=1000, interval_ms=900000)
        klines_1h = generate_klines(start_ts=1640995200000, count=250, interval_ms=3600000)

        df_15m = backtest.normalize_kline_dataframe(pd.DataFrame(klines_15m, columns=backtest.KLINE_COLUMNS))
        df_1h = backtest.normalize_kline_dataframe(pd.DataFrame(klines_1h, columns=backtest.KLINE_COLUMNS))

        symbol_frames = {
            "BTCUSDT": {
                "15m": df_15m,
                "1h": df_1h
            },
            "ETHUSDT": {
                "15m": df_15m.copy(),
                "1h": df_1h.copy()
            }
        }

        return backtest.HistoricalBinanceClient(symbol_frames)

    @pytest.mark.unit
    @pytest.mark.binance
    def test_timestamp_before_first_bar(self, setup_client_with_data):
        """Test get_klines when timestamp is before first bar."""
        client = setup_client_with_data

        # Set timestamp before any data
        client.set_current_timestamp(1000000000000)  # Way before first bar

        result = client.get_klines(symbol="BTCUSDT", interval="15m", limit=50)

        # Should return empty list or minimal data
        assert isinstance(result, list)

    @pytest.mark.unit
    @pytest.mark.binance
    def test_timestamp_after_last_bar(self, setup_client_with_data):
        """Test get_klines when timestamp is after last bar."""
        client = setup_client_with_data

        # Set timestamp far in the future
        client.set_current_timestamp(9999999999999)

        result = client.get_klines(symbol="BTCUSDT", interval="15m", limit=50)

        # Should return available bars up to limit
        assert isinstance(result, list)
        assert len(result) <= 50

    @pytest.mark.unit
    @pytest.mark.binance
    def test_timestamp_exact_match(self, setup_client_with_data):
        """Test get_klines when timestamp exactly matches a bar."""
        client = setup_client_with_data

        # Get first timestamp from data
        first_ts = 1640995200000 + 100 * 900000  # Middle timestamp

        client.set_current_timestamp(first_ts)

        result = client.get_klines(symbol="BTCUSDT", interval="15m", limit=10)

        # Should return bars up to and including this timestamp
        assert isinstance(result, list)
        assert len(result) > 0

    @pytest.mark.unit
    @pytest.mark.binance
    def test_limit_one(self, setup_client_with_data):
        """Test get_klines with limit=1."""
        client = setup_client_with_data

        client.set_current_timestamp(1640995200000 + 500 * 900000)

        result = client.get_klines(symbol="BTCUSDT", interval="15m", limit=1)

        # Should return exactly 1 bar
        assert len(result) == 1

    @pytest.mark.unit
    @pytest.mark.binance
    def test_limit_greater_than_available(self, setup_client_with_data):
        """Test get_klines with limit greater than available bars."""
        client = setup_client_with_data

        client.set_current_timestamp(1640995200000 + 10 * 900000)  # Early timestamp

        result = client.get_klines(symbol="BTCUSDT", interval="15m", limit=500)

        # Should return all available bars (less than limit)
        assert isinstance(result, list)
        assert len(result) < 500

    @pytest.mark.unit
    @pytest.mark.binance
    def test_invalid_symbol(self, setup_client_with_data):
        """Test get_klines with invalid symbol."""
        client = setup_client_with_data

        client.set_current_timestamp(1640995200000 + 100 * 900000)

        result = client.get_klines(symbol="INVALID", interval="15m", limit=50)

        # Should return empty list
        assert result == []

    @pytest.mark.unit
    @pytest.mark.binance
    def test_invalid_interval(self, setup_client_with_data):
        """Test get_klines with invalid interval."""
        client = setup_client_with_data

        client.set_current_timestamp(1640995200000 + 100 * 900000)

        result = client.get_klines(symbol="BTCUSDT", interval="5m", limit=50)

        # Should return empty list (interval not in data)
        assert result == []

    @pytest.mark.unit
    @pytest.mark.binance
    def test_before_set_timestamp(self, setup_client_with_data):
        """Test get_klines called before set_current_timestamp."""
        client = setup_client_with_data

        # Don't call set_current_timestamp

        result = client.get_klines(symbol="BTCUSDT", interval="15m", limit=50)

        # Should handle gracefully (timestamp_ms is None initially)
        assert isinstance(result, list)

    @pytest.mark.unit
    @pytest.mark.binance
    def test_current_datetime_property_none(self):
        """Test current_datetime property when timestamp_ms is None."""
        import backtest

        client = backtest.HistoricalBinanceClient({})

        # timestamp_ms should be None initially
        current_dt = client.current_datetime

        assert current_dt is None

    @pytest.mark.unit
    @pytest.mark.binance
    def test_current_datetime_property_valid(self, setup_client_with_data):
        """Test current_datetime property with valid timestamp."""
        client = setup_client_with_data

        ts_ms = 1640995200000
        client.set_current_timestamp(ts_ms)

        current_dt = client.current_datetime

        # Should convert to datetime correctly
        assert isinstance(current_dt, datetime)
        assert current_dt.timestamp() * 1000 == ts_ms

    @pytest.mark.unit
    @pytest.mark.binance
    def test_multiple_rapid_timestamp_changes(self, setup_client_with_data):
        """Test rapid timestamp changes (stress test)."""
        client = setup_client_with_data

        # Rapidly change timestamps
        for i in range(100):
            ts = 1640995200000 + i * 900000
            client.set_current_timestamp(ts)
            result = client.get_klines(symbol="BTCUSDT", interval="15m", limit=10)
            assert isinstance(result, list)

    @pytest.mark.unit
    @pytest.mark.binance
    def test_different_symbols_same_interval(self, setup_client_with_data):
        """Test querying different symbols with same interval."""
        client = setup_client_with_data

        client.set_current_timestamp(1640995200000 + 100 * 900000)

        result_btc = client.get_klines(symbol="BTCUSDT", interval="15m", limit=10)
        result_eth = client.get_klines(symbol="ETHUSDT", interval="15m", limit=10)

        # Both should return data
        assert len(result_btc) > 0
        assert len(result_eth) > 0

    @pytest.mark.unit
    @pytest.mark.binance
    def test_different_intervals_same_symbol(self, setup_client_with_data):
        """Test querying different intervals for same symbol."""
        client = setup_client_with_data

        client.set_current_timestamp(1640995200000 + 100 * 900000)

        result_15m = client.get_klines(symbol="BTCUSDT", interval="15m", limit=10)
        result_1h = client.get_klines(symbol="BTCUSDT", interval="1h", limit=10)

        # Both should return data
        assert len(result_15m) > 0
        assert len(result_1h) > 0
