"""Exchange adapter interface for multi-exchange support.

This module provides a unified interface for cryptocurrency exchanges,
allowing the bot to switch between Binance, Bitget, and other exchanges
without changing core trading logic.
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from datetime import datetime
import pandas as pd


class ExchangeAdapter(ABC):
    """Abstract base class for exchange adapters.

    All exchange-specific implementations must inherit from this class
    and implement all abstract methods.
    """

    @abstractmethod
    def get_klines(
        self,
        symbol: str,
        interval: str,
        limit: int = 500,
        **kwargs
    ) -> List[List[Any]]:
        """Fetch candlestick/kline data.

        Args:
            symbol: Trading pair symbol (e.g., "BTCUSDT")
            interval: Timeframe (e.g., "15m", "1h", "4h")
            limit: Number of candles to fetch
            **kwargs: Additional exchange-specific parameters

        Returns:
            List of klines in standard format:
            [timestamp, open, high, low, close, volume, close_time,
             quote_volume, trades, taker_base, taker_quote, ignore]
        """
        pass

    @abstractmethod
    def get_historical_klines(
        self,
        symbol: str,
        interval: str,
        start_ms: int,
        end_ms: int,
        **kwargs
    ) -> List[List[Any]]:
        """Fetch historical kline data for backtesting.

        Args:
            symbol: Trading pair symbol
            interval: Timeframe
            start_ms: Start timestamp in milliseconds
            end_ms: End timestamp in milliseconds
            **kwargs: Additional exchange-specific parameters

        Returns:
            List of klines in standard format
        """
        pass

    @abstractmethod
    def get_funding_rate(
        self,
        symbol: str,
        limit: int = 1,
        **kwargs
    ) -> List[Dict[str, Any]]:
        """Fetch funding rate for perpetual futures.

        Args:
            symbol: Trading pair symbol
            limit: Number of funding rate records to fetch
            **kwargs: Additional exchange-specific parameters

        Returns:
            List of funding rate records:
            [{"fundingRate": "0.0001", "fundingTime": 1234567890000, ...}, ...]
        """
        pass

    @abstractmethod
    def get_open_interest(
        self,
        symbol: str,
        interval: str,
        limit: int = 30,
        **kwargs
    ) -> List[Dict[str, Any]]:
        """Fetch open interest history.

        Args:
            symbol: Trading pair symbol
            interval: Timeframe
            limit: Number of records to fetch
            **kwargs: Additional exchange-specific parameters

        Returns:
            List of open interest records:
            [{"sumOpenInterest": "123.45", "timestamp": 1234567890000, ...}, ...]
        """
        pass

    @abstractmethod
    def normalize_symbol(self, symbol: str) -> str:
        """Convert symbol to exchange-specific format.

        Args:
            symbol: Standard symbol format (e.g., "BTCUSDT")

        Returns:
            Exchange-specific symbol format
        """
        pass

    @abstractmethod
    def normalize_interval(self, interval: str) -> str:
        """Convert interval to exchange-specific format.

        Args:
            interval: Standard interval (e.g., "15m", "1h", "4h")

        Returns:
            Exchange-specific interval format
        """
        pass

    @abstractmethod
    def get_exchange_name(self) -> str:
        """Return the name of the exchange.

        Returns:
            Exchange name (e.g., "binance", "bitget")
        """
        pass


class BinanceAdapter(ExchangeAdapter):
    """Binance exchange adapter."""

    def __init__(self, api_key: str, api_secret: str, testnet: bool = False):
        """Initialize Binance client.

        Args:
            api_key: Binance API key
            api_secret: Binance API secret
            testnet: Whether to use testnet (default: False)
        """
        from binance.client import Client
        self.client = Client(api_key, api_secret, testnet=testnet)
        self._exchange_name = "binance"

    def get_klines(
        self,
        symbol: str,
        interval: str,
        limit: int = 500,
        **kwargs
    ) -> List[List[Any]]:
        """Fetch klines from Binance."""
        symbol = self.normalize_symbol(symbol)
        interval = self.normalize_interval(interval)
        return self.client.get_klines(
            symbol=symbol,
            interval=interval,
            limit=limit,
            **kwargs
        )

    def get_historical_klines(
        self,
        symbol: str,
        interval: str,
        start_ms: int,
        end_ms: int,
        **kwargs
    ) -> List[List[Any]]:
        """Fetch historical klines from Binance."""
        symbol = self.normalize_symbol(symbol)
        interval = self.normalize_interval(interval)
        return self.client.get_historical_klines(
            symbol=symbol,
            interval=interval,
            start_str=start_ms,
            end_str=end_ms,
            **kwargs
        )

    def get_funding_rate(
        self,
        symbol: str,
        limit: int = 1,
        **kwargs
    ) -> List[Dict[str, Any]]:
        """Fetch funding rate from Binance."""
        symbol = self.normalize_symbol(symbol)
        return self.client.futures_funding_rate(
            symbol=symbol,
            limit=limit,
            **kwargs
        )

    def get_open_interest(
        self,
        symbol: str,
        interval: str,
        limit: int = 30,
        **kwargs
    ) -> List[Dict[str, Any]]:
        """Fetch open interest from Binance."""
        symbol = self.normalize_symbol(symbol)
        interval = self.normalize_interval(interval)
        return self.client.futures_open_interest_hist(
            symbol=symbol,
            period=interval,
            limit=limit,
            **kwargs
        )

    def normalize_symbol(self, symbol: str) -> str:
        """Binance uses format: BTCUSDT"""
        return symbol

    def normalize_interval(self, interval: str) -> str:
        """Binance uses format: 15m, 1h, 4h"""
        return interval

    def get_exchange_name(self) -> str:
        """Return exchange name."""
        return self._exchange_name


class BitgetAdapter(ExchangeAdapter):
    """Bitget exchange adapter."""

    def __init__(self, api_key: str, api_secret: str, passphrase: str, testnet: bool = False):
        """Initialize Bitget client.

        Args:
            api_key: Bitget API key
            api_secret: Bitget API secret
            api_secret: Bitget API passphrase
            testnet: Whether to use testnet (default: False)
        """
        try:
            from bitget import BitgetSync

            config = {
                'apiKey': api_key,
                'secret': api_secret,
                'password': passphrase,
            }

            if testnet:
                config['sandbox'] = True

            self.client = BitgetSync(config)
            self._exchange_name = "bitget"
            self._testnet = testnet
        except ImportError:
            raise ImportError(
                "Bitget SDK not installed. Install with: pip install bitget"
            )

    def get_klines(
        self,
        symbol: str,
        interval: str,
        limit: int = 500,
        **kwargs
    ) -> List[List[Any]]:
        """Fetch klines from Bitget using CCXT.

        Args:
            symbol: Trading pair symbol (e.g., "BTCUSDT")
            interval: Timeframe (e.g., "15m", "1h", "4h")
            limit: Number of candles to fetch (default: 500)

        Returns:
            List of klines in Binance-compatible format
        """
        symbol_normalized = self.normalize_symbol(symbol)
        timeframe = self.normalize_interval(interval)

        # Fetch OHLCV data using CCXT
        ohlcv = self.client.fetch_ohlcv(
            symbol=symbol_normalized,
            timeframe=timeframe,
            limit=limit
        )

        # Convert CCXT format [timestamp, open, high, low, close, volume]
        # to Binance format [timestamp, open, high, low, close, volume, close_time, ...]
        return self._convert_ccxt_to_binance_format(ohlcv)

    def get_historical_klines(
        self,
        symbol: str,
        interval: str,
        start_ms: int,
        end_ms: int,
        **kwargs
    ) -> List[List[Any]]:
        """Fetch historical klines from Bitget using CCXT.

        Args:
            symbol: Trading pair symbol
            interval: Timeframe
            start_ms: Start time in milliseconds
            end_ms: End time in milliseconds

        Returns:
            List of klines in Binance-compatible format
        """
        symbol_normalized = self.normalize_symbol(symbol)
        timeframe = self.normalize_interval(interval)

        # Fetch historical data using CCXT
        ohlcv = self.client.fetch_ohlcv(
            symbol=symbol_normalized,
            timeframe=timeframe,
            since=start_ms,
            limit=1000  # CCXT typically uses limit per request
        )

        # Filter by end time
        filtered = [candle for candle in ohlcv if candle[0] <= end_ms]

        return self._convert_ccxt_to_binance_format(filtered)

    def get_funding_rate(
        self,
        symbol: str,
        limit: int = 1,
        **kwargs
    ) -> List[Dict[str, Any]]:
        """Fetch funding rate from Bitget using CCXT.

        Args:
            symbol: Trading pair symbol
            limit: Number of funding rate records (default: 1)

        Returns:
            List of funding rate records in Binance-compatible format
        """
        symbol_normalized = self.normalize_symbol(symbol)

        try:
            # Fetch current funding rate using CCXT
            funding_rate = self.client.fetch_funding_rate(symbol_normalized)

            # Convert to Binance format
            result = [{
                "symbol": symbol,
                "fundingRate": str(funding_rate.get('fundingRate', 0)),
                "fundingTime": funding_rate.get('fundingTimestamp', int(funding_rate.get('timestamp', 0)))
            }]

            return result
        except Exception:
            # Return empty list on error (consistent with Binance behavior)
            return []

    def get_open_interest(
        self,
        symbol: str,
        interval: str,
        limit: int = 30,
        **kwargs
    ) -> List[Dict[str, Any]]:
        """Fetch open interest from Bitget using CCXT.

        Args:
            symbol: Trading pair symbol
            interval: Time interval (not used for current OI)
            limit: Number of records (default: 30)

        Returns:
            List of open interest records in Binance-compatible format
        """
        symbol_normalized = self.normalize_symbol(symbol)

        try:
            # Fetch current open interest using CCXT
            oi = self.client.fetch_open_interest(symbol_normalized)

            # Convert to Binance format
            result = [{
                "symbol": symbol,
                "sumOpenInterest": str(oi.get('openInterestAmount', 0)),
                "sumOpenInterestValue": str(oi.get('openInterestValue', 0)),
                "timestamp": oi.get('timestamp', 0)
            }]

            return result
        except Exception:
            # Return empty list on error
            return []

    def normalize_symbol(self, symbol: str) -> str:
        """Convert to Bitget CCXT symbol format.

        CCXT uses standard format: BTC/USDT:USDT for USDT-margined futures
        """
        # Convert from Binance format (BTCUSDT) to CCXT format (BTC/USDT:USDT)
        if symbol.endswith("USDT"):
            base = symbol[:-4]  # Remove USDT
            return f"{base}/USDT:USDT"
        return symbol

    def normalize_interval(self, interval: str) -> str:
        """Convert to CCXT timeframe format.

        CCXT uses standard timeframe notation (same as Binance for most intervals)
        """
        # CCXT timeframe format is similar to Binance
        # Just return as-is for common intervals
        return interval

    def get_exchange_name(self) -> str:
        """Return exchange name."""
        return self._exchange_name

    def _convert_ccxt_to_binance_format(self, ccxt_ohlcv: List) -> List[List[Any]]:
        """Convert CCXT OHLCV format to Binance kline format.

        CCXT format: [timestamp, open, high, low, close, volume]
        Binance format: [timestamp, open, high, low, close, volume,
                        close_time, quote_volume, trades, taker_base, taker_quote, ignore]

        Args:
            ccxt_ohlcv: OHLCV data in CCXT format

        Returns:
            Klines in Binance-compatible format
        """
        binance_klines = []
        for candle in ccxt_ohlcv:
            # CCXT: [timestamp_ms, open, high, low, close, volume]
            timestamp = int(candle[0])
            open_price = str(candle[1])
            high = str(candle[2])
            low = str(candle[3])
            close_price = str(candle[4])
            volume = str(candle[5])

            # Create Binance-compatible kline
            # Fields we don't have from CCXT are set to defaults
            binance_kline = [
                timestamp,          # 0: Open time
                open_price,         # 1: Open
                high,               # 2: High
                low,                # 3: Low
                close_price,        # 4: Close
                volume,             # 5: Volume
                timestamp + 60000,  # 6: Close time (estimate)
                "0",                # 7: Quote asset volume (not available)
                0,                  # 8: Number of trades (not available)
                "0",                # 9: Taker buy base asset volume (not available)
                "0",                # 10: Taker buy quote asset volume (not available)
                "0"                 # 11: Ignore
            ]
            binance_klines.append(binance_kline)

        return binance_klines
