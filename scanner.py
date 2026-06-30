"""
MRMC Scanner
============
Loops over every ticker in the universe × 3 timeframes,
runs the MRMC indicator, and writes signals.json.

Signal detection uses a lookback window per timeframe — any buy signal
that fired within the last N bars is captured, not just the current bar.
This prevents missing signals when the scanner isn't run every single day.

Lookback defaults (adjustable via SIGNAL_LOOKBACK below):
    daily   — 3 bars  (~3 trading days)
    weekly  — 3 bars  (~3 weeks)
    monthly — 2 bars  (~2 months)

Usage:
    python scanner.py                    # full run
    python scanner.py --quick            # first 50 US tickers, daily only
    python scanner.py --ticker AAPL      # debug single ticker
"""

import json
import time
import argparse
from datetime import datetime, timezone

import pandas as pd

from universe import build_universe
from fetcher  import fetch_ohlcv, fetch_latest_price
from indicator import run_mrmc


MARKET_DISPLAY = {"US": "US", "SS": "CN", "SZ": "CN", "HK": "CN"}
TIMEFRAMES = ["1d", "1wk", "1mo"]
TIMEFRAME_LABELS = {"1d": "daily", "1wk": "weekly", "1mo": "monthly"}
US_MIN_PRICE = 10.0

# ── Lookback window: how many recent bars to check for a buy signal ────────────
# Increase these if you scan infrequently (e.g. set weekly to 4 if you scan
# once a month and don't want to miss anything within that month).
SIGNAL_LOOKBACK = {
    "1d":  3,   # daily:   catch signals from the last 3 trading days
    "1wk": 3,   # weekly:  catch signals from the last 3 weeks
    "1mo": 2,   # monthly: catch signals from the last 2 months
}


def scan_ticker(ticker: str, market: str, timeframes: list[str]) -> list[dict]:
    """
    Scan one ticker across all timeframes.

    For each timeframe, looks back SIGNAL_LOOKBACK[tf] bars and captures
    the most recent buy signal found within that window (if any).

    Returns a list of signal dicts — one entry per timeframe where a buy
    signal fired within the lookback window.
    """
    signals = []

    for tf in timeframes:
        try:
            df = fetch_ohlcv(ticker, interval=tf)
            if df is None or len(df) < 60:
                continue

            result = run_mrmc(df)

            # Slice the lookback window
            lookback = SIGNAL_LOOKBACK[tf]
            window = result.iloc[-lookback:]

            # Check if any bar in the window fired a buy signal
            if not window["buy_signal"].any():
                continue

            # Use the most recent signal bar within the window
            signal_bars = window[window["buy_signal"] == 1]
            sig_bar = signal_bars.iloc[-1]

            # How many bars ago did this signal fire?
            # 0 = current (last) bar, 1 = one bar ago, etc.
            bars_ago = len(result) - 1 - result.index.get_loc(sig_bar.name)

            row = {
                "ticker":       ticker,
                "market":       MARKET_DISPLAY.get(market, market),
                "timeframe":    TIMEFRAME_LABELS[tf],
                "signal_date":  str(sig_bar.name.date()),
                "bars_ago":     bars_ago,
                "close":        round(float(sig_bar["close"]), 4),
                "DIFF":         round(float(sig_bar["DIFF"]), 6) if pd.notna(sig_bar["DIFF"]) else None,
                "DEA":          round(float(sig_bar["DEA"]),  6) if pd.notna(sig_bar["DEA"])  else None,
                "MACD":         round(float(sig_bar["MACD"]), 6) if pd.notna(sig_bar["MACD"]) else None,
            }
            signals.append(row)

        except Exception as e:
            print(f"  [error] {ticker} {tf}: {e}")

    return signals


def run_scan(quick: bool = False, single_ticker: str = None) -> None:
    print(f"\n{'='*60}")
    print(f"MRMC Scanner — {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}")
    print(f"{'='*60}")
    print(f"Lookback window: daily={SIGNAL_LOOKBACK['1d']}bars  "
          f"weekly={SIGNAL_LOOKBACK['1wk']}bars  "
          f"monthly={SIGNAL_LOOKBACK['1mo']}bars")

    # ── Build ticker list ──────────────────────────────────────────────────────
    if single_ticker:
        tasks = [(single_ticker, "US")]
        timeframes = TIMEFRAMES
    elif quick:
        universe = build_universe(include_us=True, include_china=False)
        tasks = [(t, "US") for t in universe["US"][:50]]
        timeframes = ["1d"]
    else:
        # US-only full run (China scanning disabled).
        universe = build_universe(include_us=True, include_china=False)
        tasks = []
        for market, tickers in universe.items():
            for t in tickers:
                tasks.append((t, market))
        timeframes = TIMEFRAMES

    print(f"Tickers to scan: {len(tasks)}  ×  timeframes: {timeframes}\n")

    buy_signals  = []
    price_cache  = {}

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
        buy_signals.extend(signals)

        time.sleep(0.15)

    # Sort by most recent signal first (bars_ago ascending)
    buy_signals.sort(key=lambda x: (x["bars_ago"], x["ticker"]))

    # ── Build output JSON ──────────────────────────────────────────────────────
    output = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "lookback": SIGNAL_LOOKBACK,
        "stats": {
            "total_scanned": len(tasks),
            "buy_signals":   len(buy_signals),
        },
        "buy_signals": buy_signals,
    }

    with open("signals.json", "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    print(f"\n✅ Done. Buy signals: {len(buy_signals)}")
    print("Saved → signals.json")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--quick",  action="store_true",
                        help="First 50 US tickers, daily only")
    parser.add_argument("--ticker", type=str, default=None,
                        help="Debug single ticker")
    args = parser.parse_args()
    run_scan(quick=args.quick, single_ticker=args.ticker)
