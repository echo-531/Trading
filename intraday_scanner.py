"""
MRMC Intraday Scanner
=====================
Scans a fixed watchlist (<50 tickers) on the 1h timeframe during
US market hours. Signals are written to docs/intraday_signals.json
and picked up by docs/intraday.html.

Lookback: 3 bars  (catches signals fired within the last 3 hourly bars)

Triggered by GitHub Actions every hour during US market hours (Mon–Fri).
Can also be run locally at any time:

    python intraday_scanner.py
    python intraday_scanner.py --ticker AAPL   # debug single ticker

Market-hours guard: the scanner checks whether US markets are currently
open before doing any work. If run outside market hours it exits cleanly
(useful for manual local runs and protects against cron drift).
"""

import json
import time
import argparse
from datetime import datetime, timezone, timedelta

import pandas as pd
import yfinance as yf
import logging

from indicator import run_mrmc
from intraday_watchlist import build_intraday_universe

# ── Silence yfinance noise ─────────────────────────────────────────────────────
logging.getLogger("yfinance").setLevel(logging.CRITICAL)
logging.getLogger("urllib3").setLevel(logging.CRITICAL)
logging.getLogger("peewee").setLevel(logging.CRITICAL)

# ── Config ─────────────────────────────────────────────────────────────────────
INTERVAL       = "1h"
PERIOD         = "60d"        # enough history for MRMC to warm up on 1h bars
MIN_BARS       = 60           # skip tickers with too little data
SIGNAL_LOOKBACK = 3           # how many recent bars to check for a signal
OUTPUT_PATH    = "docs/intraday_signals.json"

# US Eastern Time offset (no DST handling needed — GitHub Actions uses UTC)
# ET = UTC-5 (EST) / UTC-4 (EDT). We use a conservative window:
#   market open  ≈ 13:30 UTC (09:30 ET)
#   market close ≈ 20:00 UTC (16:00 ET)
MARKET_OPEN_UTC  = 13   # hour (inclusive)
MARKET_CLOSE_UTC = 20   # hour (exclusive)


# ── Market hours guard ─────────────────────────────────────────────────────────

def is_market_open(now_utc: datetime | None = None) -> bool:
    """
    Returns True if US equity markets are likely open right now.
    Checks: Mon–Fri, 13:00–20:00 UTC (covers 09:00–16:00 ET with buffer).
    Does NOT account for US public holidays.
    """
    if now_utc is None:
        now_utc = datetime.now(timezone.utc)
    if now_utc.weekday() >= 5:          # Saturday=5, Sunday=6
        return False
    return MARKET_OPEN_UTC <= now_utc.hour < MARKET_CLOSE_UTC


# ── Data fetch ─────────────────────────────────────────────────────────────────

def fetch_1h(ticker: str) -> pd.DataFrame | None:
    """
    Fetch 1h OHLCV bars for a US ticker via yfinance.
    yfinance limits 1h data to the last 730 days; PERIOD="60d" is well within that.
    """
    try:
        tkr = yf.Ticker(ticker)
        raw = tkr.history(period=PERIOD, interval=INTERVAL, auto_adjust=True)
        if raw.empty or len(raw) < MIN_BARS:
            return None
        df = raw[["Open", "High", "Low", "Close", "Volume"]].copy()
        df.columns = ["open", "high", "low", "close", "volume"]
        df.index.name = "date"
        df = df.dropna(subset=["close"])
        return df
    except Exception as e:
        print(f"  [fetch error] {ticker}: {e}")
        return None


# ── Single ticker scan ─────────────────────────────────────────────────────────

def scan_ticker(ticker: str, group: str) -> list[dict]:
    """
    Run MRMC on the 1h series for one ticker.
    Returns a list of signal dicts (0 or 1 entries).
    """
    df = fetch_1h(ticker)
    if df is None:
        return []

    try:
        result = run_mrmc(df)
    except Exception as e:
        print(f"  [indicator error] {ticker}: {e}")
        return []

    # Check the last SIGNAL_LOOKBACK bars for a buy signal
    window = result.iloc[-SIGNAL_LOOKBACK:]
    if not window["buy_signal"].any():
        return []

    # Most recent signal bar in the window
    signal_bars = window[window["buy_signal"] == 1]
    sig_bar = signal_bars.iloc[-1]

    bars_ago = len(result) - 1 - result.index.get_loc(sig_bar.name)

    # Format signal timestamp in ET (UTC-4 during EDT, UTC-5 during EST)
    # We store UTC and let the frontend localise if needed
    sig_ts = sig_bar.name
    if hasattr(sig_ts, "tzinfo") and sig_ts.tzinfo is not None:
        sig_ts_str = sig_ts.strftime("%Y-%m-%d %H:%M UTC")
    else:
        sig_ts_str = str(sig_ts)

    return [{
        "ticker":       ticker,
        "group":        group,
        "timeframe":    "1h",
        "signal_ts":    sig_ts_str,
        "bars_ago":     bars_ago,
        "close":        round(float(sig_bar["close"]), 4),
        "DIFF":         round(float(sig_bar["DIFF"]), 6) if pd.notna(sig_bar["DIFF"]) else None,
        "DEA":          round(float(sig_bar["DEA"]),  6) if pd.notna(sig_bar["DEA"])  else None,
        "MACD":         round(float(sig_bar["MACD"]), 6) if pd.notna(sig_bar["MACD"]) else None,
    }]


# ── Main ───────────────────────────────────────────────────────────────────────

def run_scan(single_ticker: str | None = None, force: bool = False) -> None:
    now_utc = datetime.now(timezone.utc)
    print(f"\n{'='*60}")
    print(f"MRMC Intraday Scanner — {now_utc.strftime('%Y-%m-%d %H:%M UTC')}")
    print(f"{'='*60}")

    # Market hours guard (skip when run outside hours unless --force)
    if not force and single_ticker is None and not is_market_open(now_utc):
        print("⏸  US markets are closed right now. Exiting without scan.")
        print("   Use --force to override.")
        return

    # Build task list
    if single_ticker:
        tasks = [(single_ticker.upper(), "debug")]
    else:
        tasks = build_intraday_universe()

    print(f"Watchlist: {len(tasks)} tickers  |  interval: {INTERVAL}  |  lookback: {SIGNAL_LOOKBACK} bars\n")

    buy_signals: list[dict] = []

    for i, (ticker, group) in enumerate(tasks):
        if i % 10 == 0 and i > 0:
            print(f"  Progress: {i}/{len(tasks)} …")
        sigs = scan_ticker(ticker, group)
        buy_signals.extend(sigs)
        if sigs:
            print(f"  ✅ {ticker} ({group}): buy signal {sigs[0]['bars_ago']} bars ago")
        time.sleep(0.2)   # polite rate limiting

    # Sort: most recent signal first
    buy_signals.sort(key=lambda x: x["bars_ago"])

    # Calculate next scheduled scan time (next whole hour during market hours)
    next_hour = (now_utc + timedelta(hours=1)).replace(minute=0, second=0, microsecond=0)

    output = {
        "generated_at":  now_utc.isoformat(),
        "next_scan_at":  next_hour.isoformat(),
        "interval":      INTERVAL,
        "lookback_bars": SIGNAL_LOOKBACK,
        "stats": {
            "total_scanned": len(tasks),
            "buy_signals":   len(buy_signals),
        },
        "buy_signals": buy_signals,
    }

    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    print(f"\n✅ Done. Buy signals: {len(buy_signals)}")
    print(f"Saved → {OUTPUT_PATH}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="MRMC Intraday Scanner")
    parser.add_argument("--ticker", type=str, default=None,
                        help="Scan a single ticker (debug mode)")
    parser.add_argument("--force",  action="store_true",
                        help="Run even if US markets are closed")
    args = parser.parse_args()
    run_scan(single_ticker=args.ticker, force=args.force)
