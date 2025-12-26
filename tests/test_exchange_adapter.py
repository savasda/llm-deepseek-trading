"""Unit tests for exchange adapter and factory.

These tests verify that the exchange adapter pattern works correctly
and that adapters can be swapped via environment variables.
"""

import pytest
import os
from unittest.mock import MagicMock, patch, Mock
from typing import List, Dict, Any

# Import adapters and factory
from exchange_adapter import ExchangeAdapter, BinanceAdapter, BitgetAdapter
from exchange_factory import (
    get_exchange_adapter,
    reset_exchange_adapter,
    get_current_exchange_name,
    _create_binance_adapter,
    _create_bitget_adapter
)
from exchange_mocks import BinanceMockResponses, BitgetMockResponses, MockExchangeClient


class TestExchangeAdapterInterface:
    """Test the abstract ExchangeAdapter interface."""

    @pytest.mark.unit
    def test_adapter_interface_methods(self):
        """Verify all required methods exist in interface."""
        required_methods = [
            'get_klines',
            'get_historical_klines',
            'get_funding_rate',
            'get_open_interest',
            'normalize_symbol',
            'normalize_interval',
            'get_exchange_name'
        ]

        for method in required_methods:
            assert hasattr(ExchangeAdapter, method), f"Missing method: {method}"


class TestBinanceAdapter:
    """Tests for Binance adapter implementation."""

    @pytest.fixture
    def mock_binance_client(self):
        """Create a mock Binance client."""
        from binance.client import Client
        mock = MagicMock(spec=Client)
        return mock

    @pytest.fixture
    def binance_adapter(self, mock_binance_client):
        """Create Binance adapter with mocked client."""
        with patch('binance.client.Client', return_value=mock_binance_client):
            adapter = BinanceAdapter(
                api_key="test_key",
                api_secret="test_secret"
            )
        return adapter

    @pytest.mark.unit
    def test_binance_adapter_initialization(self, binance_adapter):
        """Test Binance adapter can be initialized."""
        assert binance_adapter is not None
        assert binance_adapter.get_exchange_name() == "binance"

    @pytest.mark.unit
    def test_binance_get_klines(self, binance_adapter, mock_binance_client):
        """Test get_klines delegates to Binance client."""
        mock_klines = BinanceMockResponses.klines("BTCUSDT", "15m", 5)
        mock_binance_client.get_klines.return_value = mock_klines

        result = binance_adapter.get_klines("BTCUSDT", "15m", limit=5)

        assert result == mock_klines
        mock_binance_client.get_klines.assert_called_once_with(
            symbol="BTCUSDT",
            interval="15m",
            limit=5
        )

    @pytest.mark.unit
    def test_binance_get_funding_rate(self, binance_adapter, mock_binance_client):
        """Test get_funding_rate delegates to Binance client."""
        mock_funding = BinanceMockResponses.funding_rate("BTCUSDT", 3)
        mock_binance_client.futures_funding_rate.return_value = mock_funding

        result = binance_adapter.get_funding_rate("BTCUSDT", limit=3)

        assert result == mock_funding
        mock_binance_client.futures_funding_rate.assert_called_once_with(
            symbol="BTCUSDT",
            limit=3
        )

    @pytest.mark.unit
    def test_binance_get_open_interest(self, binance_adapter, mock_binance_client):
        """Test get_open_interest delegates to Binance client."""
        mock_oi = BinanceMockResponses.open_interest("BTCUSDT", "5m", 30)
        mock_binance_client.futures_open_interest_hist.return_value = mock_oi

        result = binance_adapter.get_open_interest("BTCUSDT", "5m", limit=30)

        assert result == mock_oi
        mock_binance_client.futures_open_interest_hist.assert_called_once_with(
            symbol="BTCUSDT",
            period="5m",
            limit=30
        )

    @pytest.mark.unit
    def test_binance_normalize_symbol(self, binance_adapter):
        """Test symbol normalization for Binance."""
        # Binance uses symbols as-is
        assert binance_adapter.normalize_symbol("BTCUSDT") == "BTCUSDT"
        assert binance_adapter.normalize_symbol("ETHUSDT") == "ETHUSDT"

    @pytest.mark.unit
    def test_binance_normalize_interval(self, binance_adapter):
        """Test interval normalization for Binance."""
        # Binance uses intervals as-is
        assert binance_adapter.normalize_interval("15m") == "15m"
        assert binance_adapter.normalize_interval("1h") == "1h"
        assert binance_adapter.normalize_interval("4h") == "4h"


class TestBitgetAdapter:
    """Tests for Bitget adapter implementation."""

    @pytest.mark.unit
    def test_bitget_adapter_initialization(self):
        """Test that Bitget adapter can be initialized."""
        adapter = BitgetAdapter(
            api_key="test_key",
            api_secret="test_secret",
            passphrase="test_pass"
        )
        assert adapter is not None
        assert adapter.get_exchange_name() == "bitget"

    @pytest.mark.unit
    def test_bitget_normalize_symbol(self):
        """Test Bitget symbol normalization logic."""
        adapter = BitgetAdapter(
            api_key="test_key",
            api_secret="test_secret",
            passphrase="test_pass"
        )

        # Expected behavior: BTCUSDT -> BTC/USDT:USDT (CCXT format for futures)
        test_symbol = "BTCUSDT"
        expected = "BTC/USDT:USDT"

        result = adapter.normalize_symbol(test_symbol)
        assert result == expected

    @pytest.mark.unit
    def test_bitget_interval_mapping(self):
        """Test Bitget interval normalization mapping."""
        adapter = BitgetAdapter(
            api_key="test_key",
            api_secret="test_secret",
            passphrase="test_pass"
        )

        # CCXT uses the same interval format as Binance
        assert adapter.normalize_interval("15m") == "15m"
        assert adapter.normalize_interval("1h") == "1h"
        assert adapter.normalize_interval("4h") == "4h"


class TestExchangeFactory:
    """Tests for exchange factory pattern."""

    def teardown_method(self):
        """Reset exchange adapter after each test."""
        reset_exchange_adapter()

    @pytest.mark.unit
    def test_factory_creates_binance_by_default(self):
        """Test factory creates Binance adapter by default."""
        with patch.dict('os.environ', {'BN_API_KEY': 'test', 'BN_SECRET': 'test'}, clear=True):
            with patch('binance.client.Client'):
                reset_exchange_adapter()
                adapter = get_exchange_adapter()

                assert adapter is not None
                assert adapter.get_exchange_name() == "binance"

    @pytest.mark.unit
    def test_factory_creates_binance_when_specified(self):
        """Test factory creates Binance adapter when EXCHANGE=binance."""
        with patch.dict('os.environ', {
            'EXCHANGE': 'binance',
            'BN_API_KEY': 'test_key',
            'BN_SECRET': 'test_secret'
        }, clear=True):
            with patch('binance.client.Client'):
                reset_exchange_adapter()
                adapter = get_exchange_adapter()

                assert adapter is not None
                assert adapter.get_exchange_name() == "binance"

    @pytest.mark.unit
    def test_factory_caches_adapter(self):
        """Test factory caches adapter (singleton pattern)."""
        with patch.dict('os.environ', {'BN_API_KEY': 'test', 'BN_SECRET': 'test'}, clear=True):
            with patch('binance.client.Client') as mock_client:
                reset_exchange_adapter()

                # First call
                adapter1 = get_exchange_adapter()

                # Second call
                adapter2 = get_exchange_adapter()

                # Should only create once
                assert mock_client.call_count == 1
                assert adapter1 is adapter2

    @pytest.mark.unit
    def test_factory_reset_clears_cache(self):
        """Test reset_exchange_adapter clears cached adapter."""
        with patch.dict('os.environ', {'BN_API_KEY': 'test', 'BN_SECRET': 'test'}, clear=True):
            with patch('binance.client.Client') as mock_client:
                reset_exchange_adapter()

                # First call
                get_exchange_adapter()

                # Reset
                reset_exchange_adapter()

                # Second call after reset
                get_exchange_adapter()

                # Should create twice (once before reset, once after)
                assert mock_client.call_count == 2

    @pytest.mark.unit
    def test_factory_raises_error_for_unsupported_exchange(self):
        """Test factory raises error for unsupported exchange."""
        with patch.dict('os.environ', {'EXCHANGE': 'unsupported', 'BN_API_KEY': 'test', 'BN_SECRET': 'test'}, clear=True):
            reset_exchange_adapter()

            with pytest.raises(ValueError, match="Unsupported exchange"):
                get_exchange_adapter()

    @pytest.mark.unit
    def test_get_current_exchange_name(self):
        """Test getting current exchange name."""
        with patch.dict('os.environ', {'BN_API_KEY': 'test', 'BN_SECRET': 'test'}, clear=True):
            with patch('binance.client.Client'):
                reset_exchange_adapter()
                name = get_current_exchange_name()

                assert name == "binance"


class TestMockResponses:
    """Tests for mock response generators."""

    @pytest.mark.unit
    def test_binance_mock_klines_structure(self):
        """Test Binance mock klines have correct structure."""
        klines = BinanceMockResponses.klines("BTCUSDT", "15m", 5)

        assert len(klines) == 5
        # Each kline should have 12 fields
        for kline in klines:
            assert len(kline) == 12
            assert isinstance(kline[0], int)  # timestamp
            assert isinstance(kline[1], str)  # open
            assert isinstance(kline[2], str)  # high
            assert isinstance(kline[3], str)  # low
            assert isinstance(kline[4], str)  # close
            assert isinstance(kline[5], str)  # volume

    @pytest.mark.unit
    def test_binance_mock_funding_rate_structure(self):
        """Test Binance mock funding rate has correct structure."""
        rates = BinanceMockResponses.funding_rate("BTCUSDT", 3)

        assert len(rates) == 3
        for rate in rates:
            assert "symbol" in rate
            assert "fundingRate" in rate
            assert "fundingTime" in rate
            assert rate["symbol"] == "BTCUSDT"

    @pytest.mark.unit
    def test_binance_mock_open_interest_structure(self):
        """Test Binance mock open interest has correct structure."""
        oi_records = BinanceMockResponses.open_interest("BTCUSDT", "5m", 3)

        assert len(oi_records) == 3
        for record in oi_records:
            assert "symbol" in record
            assert "sumOpenInterest" in record
            assert "timestamp" in record

    @pytest.mark.unit
    def test_bitget_mock_klines_structure(self):
        """Test Bitget mock klines have correct structure."""
        response = BitgetMockResponses.klines("BTCUSDT_UMCBL", "15m", 5)

        # Bitget wraps response
        assert "code" in response
        assert "data" in response
        assert response["code"] == "00000"

        klines = response["data"]
        assert len(klines) == 5

        # Each kline should have 7 fields (different from Binance)
        for kline in klines:
            assert len(kline) == 7

    @pytest.mark.unit
    def test_mock_client_binance_mode(self):
        """Test MockExchangeClient in Binance mode."""
        client = MockExchangeClient("binance")

        klines = client.get_klines("BTCUSDT", "15m", 10)
        assert len(klines) == 10
        assert len(klines[0]) == 12  # Binance format

        funding = client.get_funding_rate("BTCUSDT", 5)
        assert len(funding) == 5
        assert "fundingRate" in funding[0]

    @pytest.mark.unit
    def test_mock_client_bitget_mode(self):
        """Test MockExchangeClient in Bitget mode."""
        client = MockExchangeClient("bitget")

        # Klines - wrapped response
        klines = client.get_klines("BTCUSDT_UMCBL", "15m", 10)
        assert "code" in klines
        assert len(klines["data"]) == 10

        # Funding rate - unwrapped for consistency
        funding = client.get_funding_rate("BTCUSDT_UMCBL", 5)
        assert isinstance(funding, list)
        assert len(funding) == 5
