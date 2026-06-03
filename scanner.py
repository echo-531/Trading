"""
MRMC Scanner
============
Loops over every ticker in the universe × 3 timeframes,
runs the MRMC indicator, and writes signals.json.

Usage:
    python scanner.py                    # full run
    python scanner.py --quick            # SP500 only, 1d only (dev/test)
    python scanner.py --ticker AAPL      # single ticker debug
"""

import json
import time
import argparse
import traceback
from datetime import datetime, timezone

import pandas as pd

from universe import build_universe, get_sp500_tickers
from fetcher  import fetch_ohlcv, fetch_latest_price
from indicator import run_mrmc


TIMEFRAMES = ["1d", "1wk", "1mo"]
TIMEFRAME_LABELS = {"1d": "daily", "1wk": "weekly", "1mo": "monthly"}
US_MIN_PRICE = 20.0


def scan_ticker(ticker: str, market: str, timeframes: list[str]) -> list[dict]:
    """
    Scan one ticker across all timeframes.
    Returns a list of signal dicts (one per timeframe where signal fired on last bar).
    """
    signals = []

    for tf in timeframes:
        try:
            df = fetch_ohlcv(ticker, interval=tf)
            if df is None or len(df) < 60:
                continue

            result = run_mrmc(df)
            last = result.iloc[-1]

            row = {
                "ticker":       ticker,
                "market":       market,
                "timeframe":    TIMEFRAME_LABELS[tf],
                "date":         str(last.name.date()),
                "close":        round(float(last["close"]), 4),
                "buy_signal":   int(last["buy_signal"]),
                "sell_signal":  int(last["sell_signal"]),
                "DIFF":         round(float(last["DIFF"]), 6) if pd.notna(last["DIFF"]) else None,
                "DEA":          round(float(last["DEA"]),  6) if pd.notna(last["DEA"])  else None,
                "MACD":         round(float(last["MACD"]), 6) if pd.notna(last["MACD"]) else None,
            }
            signals.append(row)

        except Exception as e:
            print(f"  [error] {ticker} {tf}: {e}")
            # traceback.print_exc()

    return signals


def run_scan(quick: bool = False, single_ticker: str = None) -> None:
    print(f"\n{'='*60}")
    print(f"MRMC Scanner — {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}")
    print(f"{'='*60}")

    # ── Build ticker list ──────────────────────────────────────────────────────
    if single_ticker:
        tasks = [(single_ticker, "US")]
        timeframes = TIMEFRAMES
    elif quick:
        tickers = get_sp500_tickers()[:50]
        tasks = [(t, "US") for t in tickers]
        timeframes = ["1d"]
    else:
        universe = build_universe(include_us=True, include_china=True)
        tasks = []
        for market, tickers in universe.items():
            for t in tickers:
                tasks.append((t, market))
        timeframes = TIMEFRAMES

    print(f"Tickers to scan: {len(tasks)}  ×  timeframes: {timeframes}\n")

    all_signals  = []   # every ticker-timeframe result (for full history)
    buy_signals  = []   # only rows where buy_signal == 1
    sell_signals = []   # only rows where sell_signal == 1

    price_cache = {}    # ticker → latest price

    for i, (ticker, market) in enumerate(tasks):
        if i % 50 == 0:
            print(f"  Progress: {i}/{len(tasks)} …")

        # US price filter
        if market == "US":
            price = price_cache.get(ticker)
            if price is None:
                price = fetch_latest_price(ticker)
                price_cache[ticker] = price
            if price is None or price < US_MIN_PRICE:
                continue

        signals = scan_ticker(ticker, market, timeframes)
        all_signals.extend(signals)
        buy_signals.extend([s for s in signals if s["buy_signal"] == 1])
        sell_signals.extend([s for s in signals if s["sell_signal"] == 1])

        time.sleep(0.15)   # polite rate limit

    # ── Build output JSON ──────────────────────────────────────────────────────
    output = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "stats": {
            "total_scanned": len(tasks),
            "buy_signals":   len(buy_signals),
            "sell_signals":  len(sell_signals),
        },
        "buy_signals":  buy_signals,
        "sell_signals": sell_signals,
    }

    with open("signals.json", "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    print(f"\n✅ Done. Buy signals: {len(buy_signals)}  Sell signals: {len(sell_signals)}")
    print("Saved → signals.json")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--quick",  action="store_true", help="SP500 first 50, daily only")
    parser.add_argument("--ticker", type=str, default=None, help="Debug single ticker")
    args = parser.parse_args()
    run_scan(quick=args.quick, single_ticker=args.ticker)
