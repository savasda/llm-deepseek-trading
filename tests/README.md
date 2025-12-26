# Unit Tests for Binance Integration

This directory contains comprehensive unit tests for all Binance-related functionality in the cryptocurrency trading bot.

## Test Coverage

### 1. Binance Client Tests (`test_binance_client.py`)
- Client initialization with valid/invalid credentials
- Error handling (timeouts, network errors, API exceptions)
- Client caching mechanism
- Configuration validation (testnet mode, fee rates)

### 2. Market Data Tests (`test_binance_market_data.py`)
- Single-timeframe data fetching (`fetch_market_data()`)
- Multi-timeframe data collection (`collect_prompt_market_data()`)
- Kline data processing and conversion to DataFrames
- Funding rate and open interest extraction
- Symbol/coin mapping validation
- Interval configuration tests

### 3. Backtest Tests (`test_binance_backtest.py`)
- Kline DataFrame normalization
- Historical data caching mechanism
- HistoricalBinanceClient replay functionality
- Cache file naming and directory structure
- Multi-symbol and multi-interval support

## Running the Tests

### Install Test Dependencies

```bash
pip install -r requirements.txt
```

This will install:
- `pytest` - Testing framework
- `pytest-cov` - Coverage reporting
- `pytest-mock` - Enhanced mocking capabilities

### Run All Tests

```bash
pytest
```

### Run Binance-Specific Tests Only

```bash
pytest -m binance
```

### Run with Coverage Report

```bash
pytest --cov=. --cov-report=html --cov-report=term-missing
```

View the HTML coverage report:
```bash
open htmlcov/index.html
```

### Run Specific Test Files

```bash
# Client tests only
pytest tests/test_binance_client.py

# Market data tests only
pytest tests/test_binance_market_data.py

# Backtest tests only
pytest tests/test_binance_backtest.py
```

### Run Specific Test Classes or Functions

```bash
# Run a specific test class
pytest tests/test_binance_client.py::TestBinanceClientInitialization

# Run a specific test function
pytest tests/test_binance_client.py::TestBinanceClientInitialization::test_successful_initialization
```

### Verbose Output

```bash
pytest -v
```

### Show Print Statements

```bash
pytest -s
```

## Test Markers

Tests are marked with the following pytest markers:

- `@pytest.mark.unit` - Unit tests (isolated, no external dependencies)
- `@pytest.mark.binance` - Binance-related tests
- `@pytest.mark.integration` - Integration tests (if added in the future)

Filter by markers:
```bash
pytest -m "unit and binance"
```

## Continuous Integration

To run tests in CI/CD pipelines:

```bash
pytest --cov=. --cov-report=xml --junitxml=test-results.xml
```

## Test Structure

Each test file follows this structure:

1. **Fixtures** - Reusable test data and mock objects
2. **Test Classes** - Grouped by functionality
3. **Test Methods** - Individual test cases with descriptive names

## Mocking Strategy

Tests use `unittest.mock` to:
- Mock Binance API responses
- Simulate network errors and timeouts
- Test error handling without hitting real APIs
- Isolate units under test

## Adding New Tests

When adding Binance-related functionality:

1. Create test cases in the appropriate test file
2. Use descriptive test names: `test_<functionality>_<scenario>`
3. Add appropriate pytest markers
4. Mock external dependencies (Binance API calls)
5. Test both success and error paths

## Common Test Patterns

### Mocking Binance Client
```python
@pytest.fixture
def mock_binance_client():
    client = MagicMock()
    client.get_klines.return_value = sample_klines
    return client
```

### Testing API Errors
```python
def test_api_error_handling(mock_binance_client):
    mock_binance_client.get_klines.side_effect = BinanceAPIException(None, 400, "Error")
    result = function_under_test(mock_binance_client)
    assert result is None
```

### Testing with Environment Variables
```python
@patch.dict(os.environ, {"BN_API_KEY": "test_key", "BN_SECRET": "test_secret"})
def test_with_env_vars():
    # Test code here
    pass
```

## Known Limitations

- Tests do not connect to real Binance API (all mocked)
- Integration tests with live Binance testnet are not included
- Dashboard Binance integration is not covered (excluded in `.coveragerc`)

## Future Enhancements

- [ ] Add integration tests with Binance testnet
- [ ] Add property-based tests for data validation
- [ ] Add performance benchmarks for data processing
- [ ] Add tests for concurrent API requests
- [ ] Add tests for rate limiting and retry logic

## Troubleshooting

### Import Errors
If you get import errors, ensure you're running pytest from the project root:
```bash
cd /Users/sda/Work/homework/llm-deepseek-trading
pytest
```

### Module Not Found
Make sure all dependencies are installed:
```bash
pip install -r requirements.txt
```

### Test Failures
Run with verbose output to see detailed error messages:
```bash
pytest -vv
```

## References

- [pytest Documentation](https://docs.pytest.org/)
- [pytest-cov Documentation](https://pytest-cov.readthedocs.io/)
- [unittest.mock Documentation](https://docs.python.org/3/library/unittest.mock.html)
- [Binance API Documentation](https://binance-docs.github.io/apidocs/)
