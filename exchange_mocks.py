"""Mock responses for exchange APIs.

This module provides mock response classes that simulate real exchange API responses.
These mocks are useful for:
1. Testing without real API credentials
2. Understanding the expected data structure
3. Developing exchange adapters before SDK is available
"""

from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import random


class BinanceMockResponses:
    """Mock responses matching Binance API format."""

    @staticmethod
    def klines(
        symbol: str = "BTCUSDT",
        interval: str = "15m",
        count: int = 100,
        start_price: float = 30000.0
    ) -> List[List[Any]]:
        """Generate mock kline data matching Binance format.

        Returns list of klines where each kline is:
        [
            timestamp,      # 0: Opening timestamp (ms)
            open,           # 1: Open price (string)
            high,           # 2: High price (string)
            low,            # 3: Low price (string)
            close,          # 4: Close price (string)
            volume,         # 5: Base asset volume (string)
            close_time,     # 6: Closing timestamp (ms)
            quote_volume,   # 7: Quote asset volume (string)
            trades,         # 8: Number of trades (int)
            taker_base,     # 9: Taker buy base asset volume (string)
            taker_quote,    # 10: Taker buy quote asset volume (string)
            ignore          # 11: Unused field (string)
        ]
        """
        interval_ms = {
            "1m": 60000, "3m": 180000, "5m": 300000,
            "15m": 900000, "30m": 1800000,
            "1h": 3600000, "2h": 7200000, "4h": 14400000
        }.get(interval, 900000)

        klines = []
        current_time = int(datetime.now().timestamp() * 1000)
        current_price = start_price

        for i in range(count):
            timestamp = current_time - (count - i) * interval_ms
            close_time = timestamp + interval_ms - 1

            # Simulate price movement
            price_change = random.uniform(-0.02, 0.02)
            open_price = current_price
            close_price = current_price * (1 + price_change)
            high_price = max(open_price, close_price) * random.uniform(1.0, 1.01)
            low_price = min(open_price, close_price) * random.uniform(0.99, 1.0)

            volume = random.uniform(50, 200)
            quote_volume = volume * (open_price + close_price) / 2

            klines.append([
                timestamp,
                f"{open_price:.2f}",
                f"{high_price:.2f}",
                f"{low_price:.2f}",
                f"{close_price:.2f}",
                f"{volume:.4f}",
                close_time,
                f"{quote_volume:.2f}",
                random.randint(500, 2000),
                f"{volume * 0.5:.4f}",
                f"{quote_volume * 0.5:.2f}",
                "0"
            ])

            current_price = close_price

        return klines

    @staticmethod
    def funding_rate(
        symbol: str = "BTCUSDT",
        count: int = 1
    ) -> List[Dict[str, Any]]:
        """Generate mock funding rate data matching Binance format.

        Returns list of funding rate records:
        [
            {
                "symbol": "BTCUSDT",
                "fundingRate": "0.0001",
                "fundingTime": 1234567890000,
                ...
            }
        ]
        """
        current_time = int(datetime.now().timestamp() * 1000)
        funding_interval = 8 * 3600 * 1000  # 8 hours in milliseconds

        rates = []
        for i in range(count):
            funding_time = current_time - (count - i - 1) * funding_interval
            rates.append({
                "symbol": symbol,
                "fundingRate": f"{random.uniform(-0.0005, 0.0005):.8f}",
                "fundingTime": funding_time,
            })

        return rates

    @staticmethod
    def open_interest(
        symbol: str = "BTCUSDT",
        interval: str = "5m",
        count: int = 30
    ) -> List[Dict[str, Any]]:
        """Generate mock open interest data matching Binance format.

        Returns list of open interest records:
        [
            {
                "symbol": "BTCUSDT",
                "sumOpenInterest": "123456.789",
                "sumOpenInterestValue": "3704567890.12",
                "timestamp": 1234567890000
            }
        ]
        """
        interval_ms = {
            "5m": 300000, "15m": 900000,
            "30m": 1800000, "1h": 3600000
        }.get(interval, 300000)

        current_time = int(datetime.now().timestamp() * 1000)
        base_oi = random.uniform(100000, 200000)

        records = []
        for i in range(count):
            timestamp = current_time - (count - i) * interval_ms
            oi = base_oi * random.uniform(0.95, 1.05)
            oi_value = oi * random.uniform(29000, 31000)

            records.append({
                "symbol": symbol,
                "sumOpenInterest": f"{oi:.3f}",
                "sumOpenInterestValue": f"{oi_value:.2f}",
                "timestamp": timestamp
            })

        return records


class BitgetMockResponses:
    """Mock responses matching Bitget API format.

    Note: These are based on typical Bitget API structure.
    Verify with actual Bitget API documentation when implementing.
    """

    @staticmethod
    def klines(
        symbol: str = "BTCUSDT_UMCBL",
        interval: str = "15m",
        count: int = 100,
        start_price: float = 30000.0
    ) -> Dict[str, Any]:
        """Generate mock kline data matching Bitget format.

        Bitget typically wraps responses in {"code": "00000", "data": [...]}

        Kline format (verify with docs):
        [
            timestamp,      # Opening timestamp (string or int)
            open,           # Open price (string)
            high,           # High price (string)
            low,            # Low price (string)
            close,          # Close price (string)
            volume,         # Volume in USD (string)
            volumeCcy       # Volume in crypto (string)
        ]
        """
        interval_map = {
            "1m": "1m", "3m": "3m", "5m": "5m",
            "15m": "15m", "30m": "30m",
            "1h": "1H", "2h": "2H", "4h": "4H"
        }

        interval_ms = {
            "1m": 60000, "3m": 180000, "5m": 300000,
            "15m": 900000, "30m": 1800000,
            "1H": 3600000, "2H": 7200000, "4H": 14400000
        }.get(interval_map.get(interval, "15m"), 900000)

        current_time = int(datetime.now().timestamp() * 1000)
        current_price = start_price

        klines = []
        for i in range(count):
            timestamp = current_time - (count - i) * interval_ms

            # Simulate price movement
            price_change = random.uniform(-0.02, 0.02)
            open_price = current_price
            close_price = current_price * (1 + price_change)
            high_price = max(open_price, close_price) * random.uniform(1.0, 1.01)
            low_price = min(open_price, close_price) * random.uniform(0.99, 1.0)

            volume_usd = random.uniform(100000, 500000)
            volume_ccy = volume_usd / current_price

            klines.append([
                str(timestamp),
                f"{open_price:.2f}",
                f"{high_price:.2f}",
                f"{low_price:.2f}",
                f"{close_price:.2f}",
                f"{volume_usd:.2f}",
                f"{volume_ccy:.4f}"
            ])

            current_price = close_price

        return {
            "code": "00000",
            "msg": "success",
            "requestTime": current_time,
            "data": klines
        }

    @staticmethod
    def funding_rate(
        symbol: str = "BTCUSDT_UMCBL",
        count: int = 1
    ) -> Dict[str, Any]:
        """Generate mock funding rate data matching Bitget format."""
        current_time = int(datetime.now().timestamp() * 1000)
        funding_interval = 8 * 3600 * 1000

        rates = []
        for i in range(count):
            funding_time = current_time - (count - i - 1) * funding_interval
            rates.append({
                "symbol": symbol,
                "fundingRate": f"{random.uniform(-0.0005, 0.0005):.8f}",
                "settleTime": str(funding_time)
            })

        return {
            "code": "00000",
            "msg": "success",
            "requestTime": current_time,
            "data": rates
        }

    @staticmethod
    def open_interest(
        symbol: str = "BTCUSDT_UMCBL",
        count: int = 30
    ) -> Dict[str, Any]:
        """Generate mock open interest data matching Bitget format."""
        current_time = int(datetime.now().timestamp() * 1000)
        base_oi = random.uniform(100000, 200000)

        records = []
        for i in range(count):
            timestamp = current_time - (count - i) * 300000  # 5min intervals
            oi = base_oi * random.uniform(0.95, 1.05)

            records.append({
                "symbol": symbol,
                "amount": f"{oi:.3f}",
                "timestamp": str(timestamp)
            })

        return {
            "code": "00000",
            "msg": "success",
            "requestTime": current_time,
            "data": records
        }


class MockExchangeClient:
    """Mock exchange client for testing.

    Can simulate both Binance and Bitget responses.
    """

    def __init__(self, exchange: str = "binance"):
        """Initialize mock client.

        Args:
            exchange: "binance" or "bitget"
        """
        self.exchange = exchange.lower()
        if self.exchange == "binance":
            self.responses = BinanceMockResponses()
        elif self.exchange == "bitget":
            self.responses = BitgetMockResponses()
        else:
            raise ValueError(f"Unsupported exchange: {exchange}")

    def get_klines(self, symbol: str, interval: str, limit: int = 100, **kwargs):
        """Get mock klines."""
        return self.responses.klines(symbol, interval, limit)

    def get_historical_klines(
        self,
        symbol: str,
        interval: str,
        start_ms: int,
        end_ms: int,
        **kwargs
    ):
        """Get mock historical klines."""
        # Calculate how many bars fit in the time range
        interval_ms = {
            "1m": 60000, "3m": 180000, "5m": 300000,
            "15m": 900000, "30m": 1800000,
            "1h": 3600000, "2h": 7200000, "4h": 14400000
        }.get(interval, 900000)

        count = int((end_ms - start_ms) / interval_ms)
        return self.responses.klines(symbol, interval, min(count, 1000))

    def get_funding_rate(self, symbol: str, limit: int = 1, **kwargs):
        """Get mock funding rate."""
        if self.exchange == "binance":
            return self.responses.funding_rate(symbol, limit)
        else:
            response = self.responses.funding_rate(symbol, limit)
            return response["data"]  # Unwrap for consistency

    def get_open_interest(self, symbol: str, interval: str = "5m", limit: int = 30, **kwargs):
        """Get mock open interest."""
        if self.exchange == "binance":
            return self.responses.open_interest(symbol, interval, limit)
        else:
            response = self.responses.open_interest(symbol, limit)
            return response["data"]  # Unwrap for consistency


# Example usage and testing
if __name__ == "__main__":
    print("=== Binance Mock Responses ===\n")

    # Klines
    binance_klines = BinanceMockResponses.klines("BTCUSDT", "15m", 5)
    print("Binance Klines (5 bars):")
    for kline in binance_klines:
        print(f"  {kline[0]} | O:{kline[1]} H:{kline[2]} L:{kline[3]} C:{kline[4]} V:{kline[5]}")

    # Funding rate
    binance_funding = BinanceMockResponses.funding_rate("BTCUSDT", 3)
    print("\nBinance Funding Rate:")
    for rate in binance_funding:
        print(f"  {rate['fundingTime']}: {rate['fundingRate']}")

    # Open interest
    binance_oi = BinanceMockResponses.open_interest("BTCUSDT", "5m", 3)
    print("\nBinance Open Interest:")
    for oi in binance_oi:
        print(f"  {oi['timestamp']}: {oi['sumOpenInterest']}")

    print("\n=== Bitget Mock Responses ===\n")

    # Klines
    bitget_klines = BitgetMockResponses.klines("BTCUSDT_UMCBL", "15m", 5)
    print("Bitget Klines (5 bars):")
    print(f"  Code: {bitget_klines['code']}, Msg: {bitget_klines['msg']}")
    for kline in bitget_klines['data']:
        print(f"  {kline[0]} | O:{kline[1]} H:{kline[2]} L:{kline[3]} C:{kline[4]} V:{kline[5]}")

    # Funding rate
    bitget_funding = BitgetMockResponses.funding_rate("BTCUSDT_UMCBL", 3)
    print("\nBitget Funding Rate:")
    for rate in bitget_funding['data']:
        print(f"  {rate['settleTime']}: {rate['fundingRate']}")

    print("\n=== Mock Client Usage ===\n")

    # Test with mock client
    mock_client = MockExchangeClient("binance")
    klines = mock_client.get_klines("BTCUSDT", "15m", 3)
    print(f"Mock Client (Binance) returned {len(klines)} klines")
    print(f"First kline: {klines[0][:5]}...")
