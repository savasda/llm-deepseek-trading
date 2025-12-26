"""Unit tests for Binance client initialization and management."""

import os
from unittest.mock import MagicMock, patch, Mock
import pytest
from binance.client import Client
from binance.exceptions import BinanceAPIException
from requests.exceptions import Timeout, RequestException


@pytest.fixture(autouse=True)
def reset_bot_client():
    """Reset the bot's global client and exchange factory before each test."""
    import bot
    from exchange_factory import reset_exchange_adapter
    bot.client = None
    reset_exchange_adapter()
    yield
    bot.client = None
    reset_exchange_adapter()


@pytest.fixture
def mock_env_vars():
    """Provide mock environment variables for Binance."""
    with patch.dict(os.environ, {
        "EXCHANGE": "binance",
        "BN_API_KEY": "test_api_key",
        "BN_SECRET": "test_api_secret"
    }):
        yield


@pytest.fixture
def clear_env_vars():
    """Clear Binance environment variables."""
    with patch.dict(os.environ, {}, clear=True):
        yield


class TestBinanceClientInitialization:
    """Tests for get_binance_client() function."""

    @pytest.mark.unit
    @pytest.mark.binance
    def test_successful_initialization(self, mock_env_vars):
        """Test successful exchange client initialization."""
        # Mock the exchange factory to return a Binance adapter
        from exchange_adapter import BinanceAdapter

        with patch('binance.client.Client') as mock_client_class:
            mock_instance = MagicMock(spec=Client)
            mock_client_class.return_value = mock_instance

            # Import after patching to get fresh module state
            import bot
            from exchange_factory import reset_exchange_adapter
            reset_exchange_adapter()
            bot.client = None

            result = bot.get_binance_client()

            assert result is not None
            # Result is now an ExchangeAdapter (BinanceAdapter) not raw Client
            assert hasattr(result, 'get_klines')
            assert hasattr(result, 'get_funding_rate')
            assert hasattr(result, 'get_open_interest')
            assert hasattr(result, 'get_exchange_name')
            mock_client_class.assert_called_once_with(
                "test_api_key",
                "test_api_secret",
                testnet=False
            )

    @pytest.mark.unit
    @pytest.mark.binance
    def test_missing_api_key(self, clear_env_vars):
        """Test initialization fails when API key is missing."""
        import bot
        bot.API_KEY = ""
        bot.API_SECRET = "test_secret"
        bot.client = None

        result = bot.get_binance_client()

        assert result is None
        assert bot.client is None

    @pytest.mark.unit
    @pytest.mark.binance
    def test_missing_api_secret(self, clear_env_vars):
        """Test initialization fails when API secret is missing."""
        import bot
        bot.API_KEY = "test_key"
        bot.API_SECRET = ""
        bot.client = None

        result = bot.get_binance_client()

        assert result is None
        assert bot.client is None

    @pytest.mark.unit
    @pytest.mark.binance
    def test_missing_both_credentials(self, clear_env_vars):
        """Test initialization fails when both credentials are missing."""
        import bot
        bot.API_KEY = ""
        bot.API_SECRET = ""
        bot.client = None

        result = bot.get_binance_client()

        assert result is None
        assert bot.client is None

    @pytest.mark.unit
    @pytest.mark.binance
    def test_timeout_exception(self, mock_env_vars):
        """Test handling of timeout exception during initialization."""
        with patch('binance.client.Client') as mock_client_class:
            mock_client_class.side_effect = Timeout("Connection timed out")

            import bot
            from exchange_factory import reset_exchange_adapter
            reset_exchange_adapter()
            bot.client = None

            result = bot.get_binance_client()

            assert result is None
            assert bot.client is None

    @pytest.mark.unit
    @pytest.mark.binance
    def test_request_exception(self, mock_env_vars):
        """Test handling of network request exception during initialization."""
        with patch('binance.client.Client') as mock_client_class:
            mock_client_class.side_effect = RequestException("Network error")

            import bot
            from exchange_factory import reset_exchange_adapter
            reset_exchange_adapter()
            bot.client = None

            result = bot.get_binance_client()

            assert result is None
            assert bot.client is None

    @pytest.mark.unit
    @pytest.mark.binance
    def test_generic_exception(self, mock_env_vars):
        """Test handling of unexpected exception during initialization."""
        with patch('binance.client.Client') as mock_client_class:
            mock_client_class.side_effect = Exception("Unexpected error")

            import bot
            from exchange_factory import reset_exchange_adapter
            reset_exchange_adapter()
            bot.client = None

            result = bot.get_binance_client()

            assert result is None
            assert bot.client is None

    @pytest.mark.unit
    @pytest.mark.binance
    def test_client_cached_after_initialization(self, mock_env_vars):
        """Test that client is cached after successful initialization."""
        with patch('binance.client.Client') as mock_client_class:
            mock_instance = MagicMock(spec=Client)
            mock_client_class.return_value = mock_instance

            import bot
            from exchange_factory import reset_exchange_adapter
            reset_exchange_adapter()
            bot.client = None

            # First call should initialize
            result1 = bot.get_binance_client()
            # Second call should return cached client
            result2 = bot.get_binance_client()

            assert result1 is result2
            # Result is now an ExchangeAdapter wrapping the Client
            assert hasattr(result1, 'get_klines')
            # Should only be called once due to caching
            mock_client_class.assert_called_once()

    @pytest.mark.unit
    @pytest.mark.binance
    def test_return_existing_client(self, mock_env_vars):
        """Test that existing client is returned without re-initialization."""
        from exchange_adapter import ExchangeAdapter

        with patch('bot.Client') as mock_client_class:
            mock_adapter = MagicMock(spec=ExchangeAdapter)

            import bot
            bot.API_KEY = "test_api_key"
            bot.API_SECRET = "test_api_secret"
            bot.client = mock_adapter  # Pre-set client (now an adapter)

            result = bot.get_binance_client()

            assert result == mock_adapter
            # Should not call Client constructor when client exists
            mock_client_class.assert_not_called()


class TestBinanceClientConfiguration:
    """Tests for Binance client configuration constants."""

    @pytest.mark.unit
    @pytest.mark.binance
    def test_testnet_disabled(self):
        """Test that Binance client is configured for mainnet (not testnet)."""
        with patch('binance.client.Client') as mock_client_class:
            with patch.dict(os.environ, {
                "EXCHANGE": "binance",
                "BN_API_KEY": "test_key",
                "BN_SECRET": "test_secret"
            }):
                import bot
                from exchange_factory import reset_exchange_adapter
                reset_exchange_adapter()
                bot.client = None

                bot.get_binance_client()

                # Verify testnet=False is passed
                mock_client_class.assert_called_once()
                call_kwargs = mock_client_class.call_args[1]
                assert call_kwargs.get('testnet') is False

    @pytest.mark.unit
    @pytest.mark.binance
    def test_fee_rates_configured(self):
        """Test that fee rates are properly configured."""
        import bot

        assert hasattr(bot, 'MAKER_FEE_RATE')
        assert hasattr(bot, 'TAKER_FEE_RATE')
        assert bot.MAKER_FEE_RATE == 0.0
        assert bot.TAKER_FEE_RATE == 0.000275  # 0.0275%
