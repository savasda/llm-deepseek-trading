#!/usr/bin/env python3
"""Quick test script to verify Bitget API responses with logging."""

import os
import logging
from dotenv import load_dotenv
from exchange_factory import get_exchange_adapter

# Configure logging to show all levels including DEBUG
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

def main():
    # Load environment variables
    load_dotenv()

    print("\n" + "="*80)
    print("BITGET API CONNECTION TEST")
    print("="*80 + "\n")

    # Get exchange adapter
    print("🔧 Initializing exchange adapter...")
    adapter = get_exchange_adapter()

    print(f"✅ Using exchange: {adapter.get_exchange_name()}\n")

    # Test symbol
    test_symbol = "BTCUSDT"

    # Test 1: Get klines
    print("\n" + "-"*80)
    print("TEST 1: Fetching klines (15m, last 5 candles)")
    print("-"*80)
    try:
        klines = adapter.get_klines(test_symbol, "15m", limit=5)
        print(f"\n✅ Successfully fetched {len(klines)} klines")
        print(f"First candle: {klines[0]}")
        print(f"Last candle: {klines[-1]}")
    except Exception as e:
        print(f"\n❌ Error: {e}")

    # Test 2: Get funding rate
    print("\n" + "-"*80)
    print("TEST 2: Fetching funding rate")
    print("-"*80)
    try:
        funding = adapter.get_funding_rate(test_symbol)
        print(f"\n✅ Successfully fetched funding rate")
        print(f"Funding rate data: {funding}")
    except Exception as e:
        print(f"\n❌ Error: {e}")

    # Test 3: Get open interest
    print("\n" + "-"*80)
    print("TEST 3: Fetching open interest")
    print("-"*80)
    try:
        oi = adapter.get_open_interest(test_symbol, "5m")
        print(f"\n✅ Successfully fetched open interest")
        print(f"Open interest data: {oi}")
    except Exception as e:
        print(f"\n❌ Error: {e}")

    print("\n" + "="*80)
    print("TEST COMPLETE")
    print("="*80 + "\n")

if __name__ == "__main__":
    main()
