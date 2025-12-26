#!/bin/bash
# Startup script for Railway deployment
# Runs both the trading bot and dashboard in parallel

set -e

echo "==================================="
echo "Starting DeepSeek Trading Bot Stack"
echo "==================================="

# Function to handle shutdown gracefully
cleanup() {
    echo ""
    echo "Shutting down services..."
    kill -TERM $BOT_PID $DASHBOARD_PID 2>/dev/null || true
    wait $BOT_PID $DASHBOARD_PID 2>/dev/null || true
    echo "Services stopped"
    exit 0
}

trap cleanup SIGTERM SIGINT

# Start the trading bot in the background
echo "[$(date)] Starting trading bot..."
python bot.py &
BOT_PID=$!
echo "[$(date)] Trading bot started (PID: $BOT_PID)"

# Start the Streamlit dashboard in the background
echo "[$(date)] Starting dashboard..."
streamlit run dashboard.py \
    --server.port=${PORT:-8501} \
    --server.address=0.0.0.0 \
    --server.headless=true \
    --browser.serverAddress=0.0.0.0 \
    --server.enableCORS=false \
    --server.enableXsrfProtection=false &
DASHBOARD_PID=$!
echo "[$(date)] Dashboard started (PID: $DASHBOARD_PID)"

echo "==================================="
echo "All services running:"
echo "  - Trading Bot (PID: $BOT_PID)"
echo "  - Dashboard (PID: $DASHBOARD_PID)"
if [ -n "$RAILWAY_PUBLIC_DOMAIN" ]; then
    echo "  - Dashboard URL: https://$RAILWAY_PUBLIC_DOMAIN"
elif [ -n "$RAILWAY_STATIC_URL" ]; then
    echo "  - Dashboard URL: https://$RAILWAY_STATIC_URL"
else
    echo "  - Dashboard Port: ${PORT:-8501}"
    echo "  - Local URL: http://localhost:${PORT:-8501}"
fi
echo "==================================="

# Wait for either process to exit
wait -n $BOT_PID $DASHBOARD_PID

# If we get here, one of the processes died
EXIT_CODE=$?
echo "[$(date)] One of the services exited with code $EXIT_CODE"

# Kill the other process
cleanup
