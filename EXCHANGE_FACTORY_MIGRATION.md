# Exchange Factory Migration Guide

## Overview

The codebase has been migrated from direct Binance client usage to an exchange-agnostic factory pattern. This allows switching between multiple exchanges (Binance, Bitget, etc.) via environment variables.

## What Changed

### Architecture

**Before:**
```python
from binance.client import Client

client = Client(api_key, api_secret)
klines = client.get_klines(symbol="BTCUSDT", interval="15m")
```

**After:**
```python
from exchange_factory import get_exchange_adapter

client = get_exchange_adapter()  # Returns BinanceAdapter or BitgetAdapter
klines = client.get_klines(symbol="BTCUSDT", interval="15m")
```

### New Files Created

1. **[exchange_adapter.py](exchange_adapter.py)** - Abstract base class and concrete adapters
   - `ExchangeAdapter` - Abstract interface
   - `BinanceAdapter` - Binance implementation
   - `BitgetAdapter` - Bitget implementation (placeholder)

2. **[exchange_factory.py](exchange_factory.py)** - Factory for creating adapters
   - `get_exchange_adapter()` - Main factory function
   - Singleton pattern for caching
   - Environment-based selection

3. **[.env.example](.env.example)** - Updated with exchange configuration

### Files Modified

1. **[bot.py](bot.py)**
   - Added `get_exchange_client()` - New primary function
   - Updated `get_binance_client()` - Now a legacy wrapper
   - Changed global `client` type from `Optional[Client]` to `Optional[ExchangeAdapter]`
   - Updated API calls:
     - `futures_funding_rate()` → `get_funding_rate()`
     - `futures_open_interest_hist()` → `get_open_interest()`

2. **[backtest.py](backtest.py)**
   - Updated `ensure_cached_klines()` to accept `ExchangeAdapter`
   - Replaced direct `Client` instantiation with factory

3. **[requirements.txt](requirements.txt)**
   - Added commented `pybitget` dependency

## How to Switch Exchanges

### Using Binance (Default)

```bash
# In .env file
EXCHANGE=binance
BN_API_KEY=your_key
BN_SECRET=your_secret
```

### Using Bitget

```bash
# In .env file
EXCHANGE=bitget
BITGET_API_KEY=your_key
BITGET_API_SECRET=your_secret
BITGET_PASSPHRASE=your_passphrase

# Install Bitget SDK
pip install pybitget
```

## API Mapping

### Binance → Exchange Adapter

| Binance Method | Adapter Method | Notes |
|----------------|----------------|-------|
| `get_klines()` | `get_klines()` | Same interface |
| `get_historical_klines()` | `get_historical_klines()` | Same interface |
| `futures_funding_rate()` | `get_funding_rate()` | ✅ **Renamed** |
| `futures_open_interest_hist()` | `get_open_interest()` | ✅ **Renamed** |

### Method Signatures

```python
# Get recent klines
client.get_klines(
    symbol: str,
    interval: str,
    limit: int = 500
) -> List[List[Any]]

# Get historical klines (for backtesting)
client.get_historical_klines(
    symbol: str,
    interval: str,
    start_ms: int,
    end_ms: int
) -> List[List[Any]]

# Get funding rate
client.get_funding_rate(
    symbol: str,
    limit: int = 1
) -> List[Dict[str, Any]]

# Get open interest
client.get_open_interest(
    symbol: str,
    interval: str,
    limit: int = 30
) -> List[Dict[str, Any]]
```

## Test Migration

### Old Test Pattern

```python
def test_fetch_data():
    mock_client = MagicMock(spec=Client)
    mock_client.futures_funding_rate.return_value = [...]

    with patch('bot.get_binance_client', return_value=mock_client):
        result = bot.fetch_market_data("BTCUSDT")
```

### New Test Pattern

```python
def test_fetch_data():
    from exchange_adapter import ExchangeAdapter

    mock_adapter = MagicMock(spec=ExchangeAdapter)
    mock_adapter.get_funding_rate.return_value = [...]  # Updated method name

    with patch('bot.get_binance_client', return_value=mock_adapter):
        result = bot.fetch_market_data("BTCUSDT")
```

### Required Test Updates

1. **Method name changes**:
   - `mock_client.futures_funding_rate` → `mock_adapter.get_funding_rate`
   - `mock_client.futures_open_interest_hist` → `mock_adapter.get_open_interest`

2. **Return type checks**:
   - Instead of checking `isinstance(result, Client)`
   - Check for adapter methods: `hasattr(result, 'get_klines')`

3. **Factory caching**:
   - Add `reset_exchange_adapter()` in test teardown if needed
   - Or patch the factory directly

## Backward Compatibility

### Function Naming

- `get_binance_client()` still works - it now returns an `ExchangeAdapter` instead of raw `Client`
- This maintains compatibility with existing code that calls `get_binance_client()`

### Method Calls

The adapter interface intentionally matches Binance's core methods (`get_klines`, `get_historical_klines`), so most code works without changes.

**Only these methods were renamed for clarity**:
- `futures_funding_rate()` → `get_funding_rate()`
- `futures_open_interest_hist()` → `get_open_interest()`

## Adding New Exchanges

To add support for a new exchange (e.g., "Bybit"):

1. **Create adapter class** in `exchange_adapter.py`:

```python
class BybitAdapter(ExchangeAdapter):
    def __init__(self, api_key: str, api_secret: str):
        from pybybit import Client
        self.client = Client(api_key, api_secret)
        self._exchange_name = "bybit"

    def get_klines(self, symbol: str, interval: str, limit: int = 500):
        # Implement using Bybit API
        response = self.client.get_kline(...)
        return self._normalize_klines(response)

    # Implement other abstract methods...
```

2. **Add factory function** in `exchange_factory.py`:

```python
def _create_bybit_adapter() -> BybitAdapter:
    api_key = os.getenv("BYBIT_API_KEY")
    api_secret = os.getenv("BYBIT_API_SECRET")
    # ... validation and return
```

3. **Update factory selector**:

```python
if exchange == "binance":
    _exchange_adapter = _create_binance_adapter()
elif exchange == "bitget":
    _exchange_adapter = _create_bitget_adapter()
elif exchange == "bybit":
    _exchange_adapter = _create_bybit_adapter()
```

4. **Add credentials to `.env.example`**

## Troubleshooting

### Issue: Tests failing after migration

**Problem**: Tests expect raw `Client` object but get `ExchangeAdapter`

**Solution**:
- Update mock specs to `ExchangeAdapter`
- Check for adapter methods instead of Client instance
- Update method names (`futures_*` → `get_*`)

### Issue: Cached client not resetting in tests

**Problem**: Factory returns cached adapter from previous test

**Solution**:
```python
from exchange_factory import reset_exchange_adapter

def teardown_method(self):
    reset_exchange_adapter()
```

### Issue: Bitget adapter not implemented

**Problem**: `NotImplementedError` when using Bitget

**Solution**: Bitget adapter is a placeholder. Implementation requires:
1. Install `pybitget` SDK
2. Study Bitget API documentation
3. Implement all abstract methods in `BitgetAdapter`
4. Map Bitget responses to standard format

## Environment Variables Reference

```bash
# Exchange Selection
EXCHANGE=binance  # Options: binance, bitget

# Binance Credentials
BN_API_KEY=...
BN_SECRET=...
BN_TESTNET=false

# Bitget Credentials (when EXCHANGE=bitget)
BITGET_API_KEY=...
BITGET_API_SECRET=...
BITGET_PASSPHRASE=...
BITGET_TESTNET=false
```

## Migration Checklist

- [x] Create `ExchangeAdapter` abstract base class
- [x] Implement `BinanceAdapter`
- [x] Create `BitgetAdapter` placeholder
- [x] Implement `exchange_factory.py`
- [x] Update `bot.py` to use factory
- [x] Update `backtest.py` to use factory
- [x] Update `requirements.txt`
- [x] Create `.env.example`
- [ ] Update tests to use adapter interface
- [ ] Implement `BitgetAdapter` fully (when needed)
- [ ] Update documentation

## Benefits

1. **Easy exchange switching** - Change one environment variable
2. **Test-friendly** - Mock at adapter level, not SDK level
3. **Maintainable** - Exchange logic isolated in adapters
4. **Extensible** - Add new exchanges without touching core code
5. **Type-safe** - Abstract interface ensures all exchanges support same methods

## Next Steps

1. **Complete Bitget implementation** - When ready to migrate
2. **Update all tests** - Use adapter interface instead of raw Client
3. **Add integration tests** - Test with real exchange APIs (testnet)
4. **Performance testing** - Ensure factory doesn't add overhead
5. **Documentation** - Update README with exchange selection guide
