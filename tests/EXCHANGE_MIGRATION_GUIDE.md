# Exchange Migration Guide: Binance → Bitget (or any other exchange)

## Overview

This test suite is designed to be **exchange-agnostic**. While the tests reference "Binance" in their names and documentation, they actually test **generic exchange integration patterns** that apply to any cryptocurrency exchange.

## What These Tests Actually Validate

### 1. **Exchange Client Management**
- ✅ Client initialization with API credentials
- ✅ Credential validation (missing key, secret, both)
- ✅ Connection error handling (timeout, network, API errors)
- ✅ Client caching/singleton pattern
- ✅ Configuration management (testnet mode, fee rates)

**Migration**: Replace `get_binance_client()` with `get_bitget_client()` or `get_exchange_client()`

### 2. **Market Data Fetching**
- ✅ Real-time kline/candlestick data retrieval
- ✅ Multi-timeframe data collection (15m, 1h, 4h)
- ✅ Funding rate extraction (for perpetual futures)
- ✅ Open interest data (for futures markets)
- ✅ Empty data handling
- ✅ API exception handling

**Migration**: Update API method names but keep the same data structure validation

### 3. **Data Normalization**
- ✅ Kline DataFrame standardization
- ✅ Type conversions (string → numeric)
- ✅ NaN/invalid data handling
- ✅ Sorting and deduplication
- ✅ Timestamp precision

**Migration**: Adapt column mappings to Bitget's kline format

### 4. **Technical Indicators**
- ✅ EMA calculation
- ✅ RSI calculation
- ✅ MACD calculation
- ✅ ATR calculation
- ✅ Swing high/low detection
- ✅ Volume ratio calculations

**Migration**: NO CHANGES NEEDED - indicators are exchange-independent

### 5. **Backtesting Infrastructure**
- ✅ Historical data caching
- ✅ Cache hit/miss logic
- ✅ Data merging and deduplication
- ✅ Timestamp-based replay
- ✅ Multi-symbol support
- ✅ Multi-interval support

**Migration**: Update data download functions, keep replay logic

### 6. **Symbol/Coin Mappings**
- ✅ Symbol format conversion (BTCUSDT ↔ BTC)
- ✅ Bidirectional mapping validation
- ✅ All symbols have mappings

**Migration**: Update symbol format (e.g., Bitget uses different formats)

## Migration Checklist

### Phase 1: API Client Replacement
- [ ] Replace `binance.client.Client` with Bitget SDK
- [ ] Update import statements
- [ ] Map Binance exceptions to Bitget exceptions
- [ ] Update `get_binance_client()` → `get_bitget_client()`
- [ ] Run: `pytest tests/test_binance_client.py`

### Phase 2: Market Data Methods
- [ ] Map Binance API methods to Bitget equivalents:
  - `get_klines()` → Bitget equivalent
  - `futures_funding_rate()` → Bitget equivalent
  - `futures_open_interest_hist()` → Bitget equivalent
  - `get_historical_klines()` → Bitget equivalent
- [ ] Update response format parsing
- [ ] Run: `pytest tests/test_binance_market_data.py`

### Phase 3: Data Format Adaptation
- [ ] Update `KLINE_COLUMNS` to match Bitget's kline structure
- [ ] Verify numeric field mappings (OHLCV)
- [ ] Update `normalize_kline_dataframe()` if needed
- [ ] Run: `pytest tests/test_binance_backtest.py`

### Phase 4: Symbol Mappings
- [ ] Update `SYMBOL_TO_COIN` and `COIN_TO_SYMBOL` dicts
- [ ] Verify Bitget's symbol format (e.g., BTC_USDT vs BTCUSDT)
- [ ] Update symbol validation logic
- [ ] Run: `pytest tests/test_binance_market_data.py::TestBinanceSymbolConfiguration`

### Phase 5: Indicators (No Changes)
- [ ] Run indicator tests to confirm they still work
- [ ] Run: `pytest tests/test_binance_indicators.py`

### Phase 6: Full Integration
- [ ] Run complete test suite
- [ ] Run: `pytest tests/ -v`
- [ ] Fix any remaining failures
- [ ] Update test names from "binance" to "exchange" or "bitget"

## Example: Binance → Bitget API Mapping

| Binance Method | Bitget Equivalent | Notes |
|----------------|-------------------|-------|
| `client.get_klines(symbol, interval, limit)` | `client.market().candles(symbol, granularity, limit)` | Different parameter names |
| `client.futures_funding_rate(symbol, limit)` | `client.mix().funding_rate(symbol)` | Check response format |
| `client.get_historical_klines(...)` | Custom implementation needed | May need pagination |

## Test Adaptation Strategy

### Option 1: Rename Tests (Recommended)
```python
# Before
class TestBinanceClientInitialization:
    ...

# After
class TestExchangeClientInitialization:
    ...
```

### Option 2: Parameterized Tests
```python
@pytest.mark.parametrize("exchange", ["binance", "bitget"])
def test_client_initialization(exchange):
    client_factory = get_exchange_client_factory(exchange)
    ...
```

### Option 3: Abstract Base Classes
```python
class ExchangeIntegrationTestBase:
    """Base class for exchange integration tests."""

    @abstractmethod
    def get_client(self):
        pass

    def test_fetch_klines(self):
        client = self.get_client()
        # Test logic here

class TestBinanceIntegration(ExchangeIntegrationTestBase):
    def get_client(self):
        return get_binance_client()

class TestBitgetIntegration(ExchangeIntegrationTestBase):
    def get_client(self):
        return get_bitget_client()
```

## Data Structure Comparison

### Binance Kline Format
```python
[
    timestamp,      # 0: Opening timestamp
    open,           # 1: Open price
    high,           # 2: High price
    low,            # 3: Low price
    close,          # 4: Close price
    volume,         # 5: Base asset volume
    close_time,     # 6: Closing timestamp
    quote_volume,   # 7: Quote asset volume
    trades,         # 8: Number of trades
    taker_base,     # 9: Taker buy base asset volume
    taker_quote,    # 10: Taker buy quote asset volume
    ignore          # 11: Unused field
]
```

### Bitget Kline Format (example - verify with docs)
```python
[
    timestamp,      # 0: Opening timestamp
    open,           # 1: Open price
    high,           # 2: High price
    low,            # 3: Low price
    close,          # 4: Close price
    volume,         # 5: Volume (USD)
    volumeCcy       # 6: Volume (crypto)
]
```

**Required Changes:**
1. Update `KLINE_COLUMNS` constant
2. Adjust `normalize_kline_dataframe()` to handle different column count
3. Update DataFrame construction in tests

## Fee Structure Migration

```python
# Binance
MAKER_FEE_RATE = 0.0
TAKER_FEE_RATE = 0.000275  # 0.0275%

# Bitget (example - verify with docs)
MAKER_FEE_RATE = 0.0002    # 0.02%
TAKER_FEE_RATE = 0.0006    # 0.06%
```

Update tests in `TestBinanceClientConfiguration::test_fee_rates_configured`

## Common Pitfalls

1. **Timestamp Format**: Binance uses milliseconds, some exchanges use seconds
2. **Symbol Format**: BTCUSDT vs BTC/USDT vs BTC_USDT
3. **Interval Names**: "15m" vs "15min" vs "900" (seconds)
4. **Response Structure**: Some exchanges wrap data in {"code": 0, "data": [...]}
5. **Rate Limiting**: Different exchanges have different rate limits
6. **Pagination**: Historical data download may require different pagination logic

## Verification Commands

After migration, run these commands to verify:

```bash
# 1. Client initialization
pytest tests/test_binance_client.py -v

# 2. Market data fetching
pytest tests/test_binance_market_data.py -v

# 3. Backtest infrastructure
pytest tests/test_binance_backtest.py -v

# 4. Indicators (should work unchanged)
pytest tests/test_binance_indicators.py -v

# 5. Full suite
pytest tests/ -v --cov=bot --cov=backtest

# 6. Integration test (manual)
python bot.py  # Run for 1 cycle with Bitget
```

## Success Criteria

✅ All 107+ tests passing
✅ Coverage remains ≥ 95% for exchange functions
✅ Bot can fetch real-time data from Bitget
✅ Backtests run successfully with Bitget historical data
✅ Indicators calculate correctly
✅ No data format errors in logs

## Rollback Plan

If migration fails:
1. Keep Binance code in `bot_binance.py`
2. Create new `bot_bitget.py`
3. Use feature flags to switch between exchanges
4. Gradually migrate functionality

## Support

- Binance API Docs: https://binance-docs.github.io/apidocs/
- Bitget API Docs: https://bitgetlimited.github.io/apidoc/
- Python Binance SDK: https://python-binance.readthedocs.io/
- Python Bitget SDK: (verify latest SDK)

---

**Remember**: These tests validate **patterns and behaviors**, not specific API implementations. As long as your new exchange integration follows the same patterns (client management, data fetching, normalization, caching), all tests will pass with minimal changes.
