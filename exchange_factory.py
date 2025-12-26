"""Exchange factory for creating exchange adapters.

This module provides a factory function to instantiate the appropriate
exchange adapter based on environment configuration.
"""

import os
import logging
from typing import Optional
from exchange_adapter import ExchangeAdapter, BinanceAdapter, BitgetAdapter


# Global exchange adapter instance (singleton pattern)
_exchange_adapter: Optional[ExchangeAdapter] = None


def get_exchange_adapter(force_reload: bool = False) -> ExchangeAdapter:
    """Get the configured exchange adapter.

    This function reads the EXCHANGE environment variable and returns
    the appropriate adapter (Binance, Bitget, etc.). The adapter is
    cached after first initialization (singleton pattern).

    Args:
        force_reload: Force recreation of the adapter (default: False)

    Returns:
        Exchange adapter instance

    Raises:
        ValueError: If exchange is not supported or credentials are missing

    Environment Variables:
        EXCHANGE: Exchange name ("binance" or "bitget", default: "binance")

        For Binance:
            BN_API_KEY: Binance API key
            BN_SECRET: Binance API secret
            BN_TESTNET: Use testnet (default: "false")

        For Bitget:
            BITGET_API_KEY: Bitget API key
            BITGET_API_SECRET: Bitget API secret
            BITGET_PASSPHRASE: Bitget API passphrase
            BITGET_TESTNET: Use testnet (default: "false")
    """
    global _exchange_adapter

    # Return cached adapter if available
    if _exchange_adapter is not None and not force_reload:
        return _exchange_adapter

    # Read exchange selection from environment
    exchange = os.getenv("EXCHANGE", "binance").lower()

    logging.info(f"Initializing exchange adapter: {exchange}")

    if exchange == "binance":
        _exchange_adapter = _create_binance_adapter()
    elif exchange == "bitget":
        _exchange_adapter = _create_bitget_adapter()
    else:
        raise ValueError(
            f"Unsupported exchange: {exchange}. "
            f"Supported exchanges: binance, bitget"
        )

    logging.info(f"Exchange adapter initialized: {_exchange_adapter.get_exchange_name()}")
    return _exchange_adapter


def _create_binance_adapter() -> BinanceAdapter:
    """Create Binance adapter from environment variables.

    Returns:
        Binance adapter instance

    Raises:
        ValueError: If required credentials are missing
    """
    api_key = os.getenv("BN_API_KEY")
    api_secret = os.getenv("BN_SECRET")
    testnet = os.getenv("BN_TESTNET", "false").lower() in ("true", "1", "yes", "on")

    if not api_key or not api_secret:
        raise ValueError(
            "Binance credentials missing. "
            "Set BN_API_KEY and BN_SECRET environment variables."
        )

    return BinanceAdapter(
        api_key=api_key,
        api_secret=api_secret,
        testnet=testnet
    )


def _create_bitget_adapter() -> BitgetAdapter:
    """Create Bitget adapter from environment variables.

    Returns:
        Bitget adapter instance

    Raises:
        ValueError: If required credentials are missing
    """
    api_key = os.getenv("BITGET_API_KEY")
    api_secret = os.getenv("BITGET_API_SECRET")
    passphrase = os.getenv("BITGET_PASSPHRASE")
    testnet = os.getenv("BITGET_TESTNET", "false").lower() in ("true", "1", "yes", "on")

    if not api_key or not api_secret or not passphrase:
        raise ValueError(
            "Bitget credentials missing. "
            "Set BITGET_API_KEY, BITGET_API_SECRET, and BITGET_PASSPHRASE "
            "environment variables."
        )

    return BitgetAdapter(
        api_key=api_key,
        api_secret=api_secret,
        passphrase=passphrase,
        testnet=testnet
    )


def reset_exchange_adapter():
    """Reset the cached exchange adapter.

    Useful for testing or when switching exchanges at runtime.
    """
    global _exchange_adapter
    _exchange_adapter = None


def get_current_exchange_name() -> str:
    """Get the name of the currently active exchange.

    Returns:
        Exchange name (e.g., "binance", "bitget")
    """
    adapter = get_exchange_adapter()
    return adapter.get_exchange_name()
