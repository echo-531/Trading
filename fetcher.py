"""
Data fetcher.

Downloads forward-adjusted OHLCV data via yfinance for a given ticker
and timeframe. Returns a clean pandas DataFrame.

yfinance "possibly delisted" warnings are suppressed — those tickers
simply return None and are skipped by the scanner.

Timeframes supported: 1d, 1wk, 1mo
Forward-adjusted prices are the yfinance default (auto_adjust=True).
"""

import logging
import time

import yfinance as yf
import pandas as pd

# ── Silence yfinance / urllib3 noise (delisted warnings, etc.) ────────────────
logging.getLogger("yfinance").setLevel(logging.CRITICAL)
logging.getLogger("urllib3").setLevel(logging.CRITICAL)
logging.getLogger("peewee").setLevel(logging.CRITICAL)


TIMEFRAME_MAP = {
    "daily":   "1d",
    "weekly":  "1wk",
    "monthly": "1mo",
}

# How many bars to fetch — enough for the MRMC indicator to warm up
LOOKBACK = {
    "1d":  500,   # ~2 years of daily bars
    "1wk": 260,   # 5 years of weekly bars
    "1mo": 120,   # 10 years of monthly bars
}


def fetch_ohlcv(ticker: str, interval: str = "1d", period: str = None) -> pd.DataFrame | None:
    """
    Fetch OHLCV data for one ticker.

    Args:
        ticker:   e.g. "AAPL", "600519.SS"
        interval: "1d", "1wk", or "1mo"
        period:   yfinance period string, e.g. "2y". Auto-selected if None.

    Returns:
        DataFrame with columns [open, high, low, close, volume] and DatetimeIndex,
        or None if data is unavailable / too short.
    """
    if period is None:
        if interval == "1d":
            period = "2y"
        elif interval == "1wk":
            period = "5y"
        else:
            period = "10y"

    try:
        tkr = yf.Ticker(ticker)
        raw = tkr.history(period=period, interval=interval, auto_adjust=True)
        if raw.empty or len(raw) < 50:
            return None

        df = raw[["Open", "High", "Low", "Close", "Volume"]].copy()
        df.columns = ["open", "high", "low", "close", "volume"]
        df.index.name = "date"
        df = df.dropna(subset=["close"])
        return df

    except Exception as e:
        print(f"  [fetch error] {ticker} {interval}: {e}")
        return None


def fetch_latest_price(ticker: str) -> float | None:
    """Return latest close price (for US price filter)."""
    try:
        tkr = yf.Ticker(ticker)
        hist = tkr.history(period="5d", interval="1d", auto_adjust=True)
        if hist.empty:
            return None
        return float(hist["Close"].dropna().iloc[-1])
    except Exception:
        return None


def is_alive(ticker: str) -> bool:
    """
    Quick check: does this ticker have recent price data?
    Used by universe.py --clean to filter out delisted stocks.
    Returns True if yfinance returns at least 1 bar in the last 30 days.
    """
    try:
        tkr = yf.Ticker(ticker)
        hist = tkr.history(period="1mo", interval="1d", auto_adjust=True)
        return not hist.empty and len(hist) >= 1
    except Exception:
        return False
