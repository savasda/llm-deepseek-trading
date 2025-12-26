# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a cryptocurrency paper-trading bot (with optional Hyperliquid mainnet execution) that uses DeepSeek LLM for trade decision-making via the OpenRouter API. The bot runs against Binance for market data and uses multi-timeframe technical analysis (15m/1H/4H) to generate trading signals.

**Live deployment**: [trades-trend.com](https://trades-trend.com/algotrading-what-is-it)

## Core Architecture

### Main Components

1. **bot.py** (2400+ lines) - Main trading loop
   - Fetches market data from Binance every 15 minutes (configurable)
   - Calculates technical indicators (EMA, RSI, MACD, ATR) across multiple timeframes
   - Calls DeepSeek API via OpenRouter with formatted market data
   - Executes trades based on AI decisions (paper or live via Hyperliquid)
   - Manages portfolio state, positions, risk management, stop-loss/take-profit
   - Logs everything to CSV files in `data/` directory
   - Sends Telegram notifications (optional)

2. **backtest.py** (800+ lines) - Historical replay harness
   - Downloads and caches Binance historical klines
   - Replays past market data bar-by-bar
   - Reuses live trading execution engine for consistency
   - Writes results to isolated `data-backtest/run-<id>/` directories
   - Generates `backtest_results.json` summary per run

3. **hyperliquid_client.py** - Hyperliquid mainnet integration
   - Wraps hyperliquid-python-sdk for live order execution
   - Supports isolated margin, IOC (market-like) orders
   - Attaches reduce-only stop-loss and take-profit triggers
   - Falls back to paper trading if initialization fails

4. **dashboard.py** - Streamlit monitoring interface
   - Real-time portfolio metrics, equity curves
   - Trade history, AI decision logs
   - Sharpe and Sortino ratio calculations
   - BTC buy-and-hold benchmark comparison

### Data Persistence

All runtime data is stored in the `data/` directory (configurable via `TRADEBOT_DATA_DIR`):
- `portfolio_state.json` - Current balance, positions, equity
- `portfolio_state.csv` - Historical portfolio snapshots
- `trade_history.csv` - All executed trades with entry/exit details
- `ai_decisions.csv` - AI signals (entry/hold/close) with reasoning
- `ai_messages.csv` - Full LLM request/response logs

Backtest data goes to `data-backtest/` (configurable via `BACKTEST_DATA_DIR`).

### Multi-Timeframe System

The bot analyzes three timeframes hierarchically:
- **4H (Trend)**: Overall bias (bullish/bearish/neutral), major EMAs, ATR for stops
- **1H (Structure)**: Swing highs/lows, pullback identification, support/resistance
- **15M (Execution)**: Precise entry timing, RSI14, MACD crossovers

Trading logic is defined in system prompts (see `prompts/system_prompt.txt`).

## Common Development Commands

### Running the Bot

**Local development:**
```bash
# Install dependencies
pip install -r requirements.txt

# Run trading bot (requires .env with API keys)
python bot.py

# Run Streamlit dashboard
streamlit run dashboard.py
```

**Docker (recommended):**
```bash
# Build image
docker build -t tradebot .

# Run bot (paper trading by default)
docker run --rm -it \
  --env-file .env \
  -v "$(pwd)/data:/app/data" \
  tradebot

# Run dashboard (access at http://localhost:8501)
docker run --rm -it \
  --env-file .env \
  -v "$(pwd)/data:/app/data" \
  -p 8501:8501 \
  tradebot \
  streamlit run dashboard.py
```

### Backtesting

**Local backtest:**
```bash
python backtest.py
```

**Docker backtest (with script helper):**
```bash
./scripts/run_backtest_docker.sh 2024-01-01T00:00:00Z 2024-01-07T00:00:00Z prompts/system_prompt.txt

# Custom interval and run ID
BACKTEST_INTERVAL=5m BACKTEST_RUN_ID=my-test \
  ./scripts/run_backtest_docker.sh 2024-02-01T00:00:00Z 2024-02-05T00:00:00Z -
```

Results are written to `data-backtest/run-<id>/` with the same CSV structure as live runs.

### Portfolio Reconciliation

If you manually edit `data/trade_history.csv`:
```bash
python scripts/recalculate_portfolio.py

# Options
python scripts/recalculate_portfolio.py --dry-run
python scripts/recalculate_portfolio.py --start-capital 7500
```

This replays the trade log to rebuild `portfolio_state.json`.

### Hyperliquid Live Trading Smoke Test

Test live trading with minimal capital:
```bash
# Requires HYPERLIQUID_LIVE_TRADING=true and credentials in .env
python scripts/manual_hyperliquid_smoke.py --coin BTC --notional 2 --leverage 1
```

## Configuration

All configuration is via environment variables (`.env` file):

### Required
- `BN_API_KEY`, `BN_SECRET` - Binance API credentials
- `OPENROUTER_API_KEY` - For DeepSeek API access

### Trading Behavior
- `TRADEBOT_INTERVAL` - Trading timeframe (3m, 5m, 15m, 30m, 1h, 4h)
- `TRADEBOT_SYSTEM_PROMPT_FILE` - Path to system prompt (default: `prompts/system_prompt.txt`)
- `TRADEBOT_SYSTEM_PROMPT` - Inline system prompt (overrides file)
- `PAPER_START_CAPITAL` - Initial paper trading balance (default: 10000.0)

### LLM Configuration
- `TRADEBOT_LLM_MODEL` - OpenRouter model ID (default: `deepseek/deepseek-chat-v3.1`)
- `TRADEBOT_LLM_TEMPERATURE` - Sampling temperature (default: 0.7)
- `TRADEBOT_LLM_MAX_TOKENS` - Max response tokens (default: 4000)
- `TRADEBOT_LLM_THINKING` - JSON thinking budget config (optional)

### Hyperliquid Live Trading (DANGER: real money)
- `HYPERLIQUID_LIVE_TRADING` - Enable live trading (default: false)
- `HYPERLIQUID_WALLET_ADDRESS` - Ethereum wallet address
- `HYPERLIQUID_PRIVATE_KEY` - Private key for signing
- `HYPERLIQUID_CAPITAL` - Initial live capital (default: 500.0)

### Backtest Configuration
All backtest settings use `BACKTEST_*` prefix to avoid interfering with live settings:
- `BACKTEST_DATA_DIR` - Data directory (default: `data-backtest/`)
- `BACKTEST_START` / `BACKTEST_END` - UTC timestamps (e.g., `2024-01-01T00:00:00Z`)
- `BACKTEST_INTERVAL` - Primary bar size (default: 15m)
- `BACKTEST_START_CAPITAL` - Initial equity (default: 10000.0)
- `BACKTEST_LLM_MODEL`, `BACKTEST_TEMPERATURE`, `BACKTEST_MAX_TOKENS`, `BACKTEST_LLM_THINKING` - Override LLM settings for backtests
- `BACKTEST_SYSTEM_PROMPT`, `BACKTEST_SYSTEM_PROMPT_FILE` - Override system prompt for backtests
- `BACKTEST_DISABLE_TELEGRAM` - Silence notifications during simulation

### Notifications (Optional)
- `TELEGRAM_BOT_TOKEN` - Telegram bot token
- `TELEGRAM_CHAT_ID` - General notification chat ID
- `TELEGRAM_SIGNALS_CHAT_ID` - Dedicated signals chat ID (rich formatted entry/exit messages)

### Risk Metrics
- `SORTINO_RISK_FREE_RATE` - Annualized risk-free rate for Sortino ratio (default: 0.0)

## Important Code Patterns

### Environment Variable Parsing
The bot uses helper functions for robust env parsing:
- `_parse_bool_env()` - Handles "true"/"1"/"yes"/"on" variations
- `_parse_float_env()` - Float parsing with fallback and warnings
- `_parse_int_env()` - Integer parsing with fallback
- `_parse_thinking_env()` - JSON/number/string parsing for LLM thinking config

Warnings are collected in `EARLY_ENV_WARNINGS` and displayed at startup.

### State Management
- `load_state()` - Loads portfolio from `portfolio_state.json`
- `save_state()` - Persists balance, positions, equity to JSON
- `reset_state()` - Reinitializes portfolio (rarely used)
- `log_portfolio_state()` - Appends snapshot to `portfolio_state.csv`

Never directly modify the global `portfolio` dict without calling `save_state()` afterward.

### Position Management
Positions are stored in `portfolio["positions"]` as:
```python
{
    "coin": "ETH",
    "side": "long",
    "entry_price": 3000.0,
    "quantity": 1.5,
    "leverage": 5,
    "stop_loss": 2880.0,
    "take_profit": 3150.0,
    "margin": 900.0,
    "entry_fee": 4.5,
    "risk_usd": 150.0,
    "invalidation_condition": "...",
}
```

### AI Decision Contract
DeepSeek must respond with JSON only (no markdown fences):
```json
{
  "ETH": {
    "signal": "entry",  // or "hold" or "close"
    "side": "long",
    "quantity": 0.5,
    "profit_target": 3150.0,
    "stop_loss": 2880.0,
    "leverage": 5,
    "confidence": 0.72,
    "risk_usd": 150.0,
    "invalidation_condition": "If price closes below 4h EMA20",
    "justification": "..."
  }
}
```

The bot validates decisions in `process_ai_decisions()` and rejects trades violating risk rules.

### Timeframe Data Fetching
The bot fetches three timeframes for each symbol:
- 200 bars of 15m candles (execution)
- 100 bars of 1h candles (structure)
- 100 bars of 4h candles (trend)

Data is formatted into a rich prompt via `format_prompt_for_deepseek()` with hierarchy markers.

### Indicator Calculations
Technical indicators are computed using pandas in `calculate_indicators()`:
- EMAs: 20, 50, 200 period
- RSI: 14 period
- MACD: 12/26/9 standard settings
- ATR: 14 period

Swing highs/lows are identified using rolling windows on 1h data.

### Backtesting Time Control
Backtest injects a custom time provider via `set_time_provider()` to override `get_current_time()`. This allows the bot to think it's running live while actually replaying historical data.

## Testing Strategy

There are no unit tests in this repository. Testing is primarily done through:
1. **Manual paper trading** - Run bot.py in default mode
2. **Historical backtests** - Use backtest.py to evaluate on past data
3. **Hyperliquid smoke tests** - scripts/manual_hyperliquid_smoke.py with minimal capital
4. **Dashboard validation** - Visual inspection of metrics in Streamlit UI

When making changes, validate by running a short backtest before deploying to live paper trading.

## Symbols and Market Coverage

Currently trading 6 perpetual pairs (hardcoded in `bot.py:132`):
- ETHUSDT, SOLUSDT, XRPUSDT, BTCUSDT, DOGEUSDT, BNBUSDT

Mappings are maintained in `SYMBOL_TO_COIN` and `COIN_TO_SYMBOL` dicts. Hyperliquid uses coin names (ETH, BTC) while Binance uses full symbols (ETHUSDT).

## Important Files

- `prompts/system_prompt.txt` - Main trading strategy rules (multi-timeframe logic)
- `prompts/system_prompt_sniper.txt` - Alternative strategy example
- `file example -> .env.example` - Template for environment variables
- `hyperliquid.md` - Detailed Hyperliquid integration documentation

## Risk Management Notes

The bot enforces:
- Maximum 2% risk per trade (configurable via system prompt)
- Mandatory stop-loss on every position
- Leverage validation before entry
- Free margin checks (positions rejected if insufficient capital)
- 20% stop-loss proximity rule (don't close manually if within 20% of SL distance)

Exit only occurs when:
1. Stop loss or take profit is hit
2. 1H structure breaks (price closes beyond swing_high/swing_low)
3. 4H major trend reverses (closes beyond EMA50 + MACD flip)

## Live Trading Warnings

- **Paper trading is the default and recommended mode**
- Hyperliquid live trading requires `HYPERLIQUID_LIVE_TRADING=true` and wallet credentials
- Private keys should never be committed to version control
- Use a dedicated trading wallet with limited funds
- Live mode attaches real stop-loss and take-profit triggers on Hyperliquid mainnet
- If SDK initialization fails, the bot falls back to paper trading with a warning

## Contact

- Email: contact@trades-trend.com
- Telegram: @tot_gromov
