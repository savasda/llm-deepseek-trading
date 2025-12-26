# Railway Deployment Guide

This guide covers deploying the DeepSeek Trading Bot to [Railway](https://railway.com), a modern cloud platform that simplifies deployment and hosting.

## Overview

Railway provides:
- Automatic deployment from GitHub
- Built-in environment variable management
- Persistent storage with volumes
- Automatic HTTPS and custom domains
- Single service running both bot and dashboard
- Free tier with $5 monthly credit

## Architecture

The deployment uses a **single Railway service** that runs both:
1. **Trading Bot** - Background process executing trades (`bot.py`)
2. **Streamlit Dashboard** - Web interface for monitoring (`dashboard.py`)

Both processes run in parallel in the same container, sharing data through `/app/data`. The dashboard serves as the health check endpoint, ensuring the deployment is marked as healthy once Streamlit is ready.

## Prerequisites

1. **Railway Account** - Sign up at [railway.com](https://railway.com)
2. **GitHub Repository** - Your code must be in a GitHub repository
3. **API Credentials** - Have your Binance and OpenRouter API keys ready

## Step-by-Step Deployment

### 1. Create a New Project

1. Log in to Railway
2. Click **"New Project"**
3. Select **"Deploy from GitHub repo"**
4. Authorize Railway to access your GitHub account
5. Select your trading bot repository

### 2. Configure the Service

1. Railway will automatically detect the Dockerfile and deploy
2. The service will run both the trading bot and dashboard via `start.sh`
3. Go to **Settings** tab:
   - **Public Networking**: Enabled by default (needed for dashboard access)
   - Railway will assign a public URL automatically
4. Go to **Variables** tab and add all required environment variables:

```bash
# Exchange Configuration
EXCHANGE=binance
BN_API_KEY=your_binance_api_key
BN_SECRET=your_binance_secret
BN_TESTNET=false

# LLM Configuration
OPENROUTER_API_KEY=your_openrouter_key
TRADEBOT_LLM_MODEL=deepseek/deepseek-chat-v3.1
TRADEBOT_LLM_TEMPERATURE=0.7
TRADEBOT_LLM_MAX_TOKENS=4000

# Trading Configuration
TRADEBOT_INTERVAL=15m
TRADEBOT_SYSTEM_PROMPT_FILE=prompts/system_prompt.txt
PAPER_START_CAPITAL=10000.0

# Data Directory
TRADEBOT_DATA_DIR=/app/data

# Optional: Telegram Notifications
TELEGRAM_BOT_TOKEN=your_telegram_bot_token
TELEGRAM_CHAT_ID=your_chat_id
TELEGRAM_SIGNALS_CHAT_ID=your_signals_chat_id

# Optional: Hyperliquid Live Trading (DANGER!)
HYPERLIQUID_LIVE_TRADING=false
# HYPERLIQUID_WALLET_ADDRESS=0x...
# HYPERLIQUID_PRIVATE_KEY=...
# HYPERLIQUID_CAPITAL=500.0
```

5. Go to **Volumes** tab:
   - Click **"New Volume"**
   - Set mount path: `/app/data`
   - This ensures your trading data persists across deployments

### 3. Deploy and Access

1. The service will automatically build and deploy
2. Monitor the deployment logs to see both bot and dashboard starting
3. Once deployed, Railway provides a public URL
4. **Find your dashboard URL**:
   - Click on your service in Railway dashboard
   - Look for the **Deployments** section - you'll see a URL like `https://your-app.up.railway.app`
   - Or go to **Settings** → **Networking** → **Public Networking** to see the generated domain
5. Click on the URL to access your live dashboard in your browser
6. The trading bot runs in the background of the same container

You should see logs showing both processes starting:
```
Starting DeepSeek Trading Bot Stack
Starting trading bot...
Starting dashboard...
All services running
```

**Your dashboard will be publicly accessible at the Railway-provided HTTPS URL** (e.g., `https://llm-deepseek-trading-production.up.railway.app`)

## Environment Variable Management

### Using Railway UI

Add variables through the Railway dashboard:
1. Select a service
2. Go to **Variables** tab
3. Click **"New Variable"**
4. Enter key-value pairs

### Using Railway CLI (Advanced)

Install Railway CLI:
```bash
npm install -g @railway/cli
```

Link your project:
```bash
railway link
```

Set variables:
```bash
railway variables set BN_API_KEY=your_key
railway variables set OPENROUTER_API_KEY=your_key
```

## Volume Management

### Data Persistence

Railway volumes ensure your trading data persists across deployments:
- `portfolio_state.json` - Current portfolio state
- `portfolio_state.csv` - Historical snapshots
- `trade_history.csv` - All executed trades
- `ai_decisions.csv` - AI trading signals
- `ai_messages.csv` - Full LLM logs

Both the trading bot and dashboard read/write to the same `/app/data` directory, ensuring the dashboard always shows **live, real-time data**.

### Accessing Volume Data

To download data from Railway volumes:

1. Install Railway CLI
2. Connect to your service:
```bash
railway run bash
```

3. From within the container:
```bash
cat /app/data/portfolio_state.json
cat /app/data/trade_history.csv
```

### Backing Up Data

Use Railway CLI to copy files:
```bash
# Connect and copy a file
railway run cat /app/data/portfolio_state.json > backup_portfolio.json
railway run cat /app/data/trade_history.csv > backup_trades.csv
```

## Custom Domain (Optional)

1. Go to your service **Settings**
2. Scroll to **Networking** section
3. Click **"Generate Domain"** for a Railway subdomain
4. Or add a **Custom Domain** if you own one:
   - Click **"Custom Domain"**
   - Enter your domain (e.g., `trading.yourdomain.com`)
   - Add the CNAME record shown to your DNS provider
   - Railway automatically provisions SSL certificates

## Monitoring and Logs

### View Logs

1. Click on your service
2. Go to **Deployments** tab
3. Click on the latest deployment
4. View real-time logs showing both bot and dashboard output

### Using Railway CLI

```bash
# View service logs
railway logs

# Follow logs in real-time (see both bot and dashboard)
railway logs --follow
```

You'll see interleaved logs from both processes:
- Trading bot: Trade execution, AI decisions, portfolio updates
- Dashboard: Streamlit startup, HTTP requests, user interactions

## Scaling and Resource Management

### Adjust Resources

1. Go to service **Settings**
2. Scroll to **Resources** section
3. Adjust:
   - Memory limit (default: 512MB, recommend: 1GB)
   - CPU shares (default: 1 vCPU)
   - Replica count (default: 1)

### Cost Optimization

- Free tier: $5/month credit (sufficient for light usage)
- Pro plan: $20/month (includes more resources and priority support)
- Monitor usage in **Project Settings > Usage**

## Troubleshooting

### Service Not Starting

1. Check logs for errors:
   ```bash
   railway logs
   ```

2. Verify environment variables are set correctly (especially API keys)

3. Ensure volume is mounted at `/app/data`

4. Check that both processes started in the logs:
   - Look for "Starting trading bot..."
   - Look for "Starting dashboard..."

### Dashboard Not Loading

1. Check if public networking is enabled in Settings
2. Verify `PORT` environment variable exists (auto-generated by Railway)
3. Wait for health check at `/` to pass (can take 2-3 minutes on first deploy)
4. Check logs for Streamlit startup errors
5. Click on the **Settings** → **Networking** to find your public URL

### Data Not Persisting

1. Verify volume is mounted to `/app/data` in the Volumes tab
2. Check `TRADEBOT_DATA_DIR=/app/data` is set in environment variables
3. Look for file write errors in the logs

### Out of Memory Errors

1. Increase memory limit in service settings
2. Reduce `TRADEBOT_LLM_MAX_TOKENS` to use less memory
3. Consider upgrading to Railway Pro plan

### API Connection Issues

1. Verify API keys are correct
2. Check Railway logs for specific error messages
3. Ensure Binance/OpenRouter APIs are accessible from Railway's infrastructure

## CI/CD and Auto-Deployment

Railway automatically redeploys when you push to GitHub:

1. Go to service **Settings**
2. Under **Deploy** section:
   - **Watch Paths**: Optionally specify which files trigger redeploys
   - **Build Command**: Uses Dockerfile by default
   - **Restart Policy**: Set to restart on failure

### Manual Deployment

Trigger manual deployment:
```bash
railway up
```

This will rebuild and redeploy your service, restarting both the bot and dashboard.

## Security Best Practices

1. **Never commit API keys** - Always use Railway environment variables
2. **Use testnet first** - Set `BN_TESTNET=true` for initial testing
3. **Limit Hyperliquid capital** - If using live trading, start with minimal funds
4. **Enable Telegram alerts** - Get notified of all trades
5. **Regularly backup data** - Download volume data periodically
6. **Use dedicated API keys** - Create Railway-specific API keys with limited permissions

## Advanced Configuration

### Multiple Environments

Create separate Railway projects for:
- **Development** - Testing with testnet/paper trading
- **Production** - Live paper trading or real trading

Each project can have different environment variables and configurations.

### Database Integration (Optional)

For advanced analytics, connect PostgreSQL:
1. Add **PostgreSQL** service in Railway project
2. Modify bot to write to database in addition to CSV
3. Build custom analytics queries
4. Both services share the same database connection

## Cost Estimation

### Free Tier Usage
- Single service running both bot + dashboard: ~$3-5/month (24/7)
- Volume storage: Included
- Network egress: Minimal (API calls only)
- **Total**: Within $5 free credit for light usage

### Pro Tier Usage
- Increased resources and support
- $20/month base + usage
- Better for production deployments with higher resource needs

## Support and Resources

- **Railway Documentation**: [docs.railway.app](https://docs.railway.app)
- **Railway Discord**: [discord.gg/railway](https://discord.gg/railway)
- **Trading Bot Issues**: [GitHub Issues](https://github.com/yourusername/llm-deepseek-trading/issues)
- **Email**: contact@trades-trend.com
- **Telegram**: @tot_gromov

## Migration from Docker

If you're currently running with Docker locally:

1. Your `Dockerfile` works as-is on Railway (now uses `start.sh` for both processes)
2. Export environment variables from `.env`:
   ```bash
   cat .env
   ```
3. Copy each variable to Railway dashboard
4. Create a volume at `/app/data`
5. Deploy and verify both bot and dashboard are running
6. Access the public URL to see your dashboard
7. Optionally migrate local `data/` files to Railway volume

## Next Steps

After deployment:

1. **Access the dashboard** at your Railway-provided URL
2. **Monitor logs** to see both bot and dashboard output
3. **Verify trading activity** - Check that trades are being logged
4. **Set up Telegram notifications** for mobile alerts
5. **Run backtests locally** to optimize your strategy
6. **Add a custom domain** for easier access
7. **Set up data backups** using Railway CLI

The dashboard will show live data as the bot executes trades in real-time!

## Disclaimer

Running live trading bots involves financial risk. Always test thoroughly in paper trading mode before enabling live trading. Railway deployment does not reduce trading risks - you are solely responsible for all trading decisions and outcomes.
