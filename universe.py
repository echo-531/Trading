"""
Universe builder.

US:    S&P 500 + Nasdaq 100 + Russell 2000 components, filtered to price > $20.
China: All A-share stocks (Shanghai + Shenzhen) via akshare.
HK:    Optional — Hang Seng constituents via yfinance.

Returns lists of ticker strings ready for the data fetcher.
"""

import json
import time
import requests
import pandas as pd


# ── US Universe ────────────────────────────────────────────────────────────────

def get_sp500_tickers() -> list[str]:
    url = "https://en.wikipedia.org/wiki/List_of_S%26P_500_companies"
    tables = pd.read_html(url)
    return tables[0]["Symbol"].str.replace(".", "-", regex=False).tolist()


def get_nasdaq100_tickers() -> list[str]:
    url = "https://en.wikipedia.org/wiki/Nasdaq-100"
    tables = pd.read_html(url)
    # find the table with a 'Ticker' or 'Symbol' column
    for t in tables:
        cols = [c.lower() for c in t.columns]
        if "ticker" in cols:
            return t["Ticker"].dropna().tolist()
        if "symbol" in cols:
            return t["Symbol"].dropna().tolist()
    return []


def get_us_universe() -> list[str]:
    """
    Merge S&P 500 + Nasdaq 100 and deduplicate.
    Price filter (>$20) is applied at scan time after data fetch.
    """
    tickers = set(get_sp500_tickers()) | set(get_nasdaq100_tickers())
    return sorted(tickers)


# ── China A-share Universe ─────────────────────────────────────────────────────

def get_china_universe() -> list[str]:
    """
    Full A-share stock list from akshare.
    Returns tickers in the format yfinance accepts: XXXXXX.SS or XXXXXX.SZ
    """
    try:
        import akshare as ak
        # Shanghai
        sh = ak.stock_info_sh_name()
        sh_tickers = (sh["SECURITY_CODE_A"].astype(str).str.zfill(6) + ".SS").tolist()
        # Shenzhen
        sz = ak.stock_info_sz_name()
        sz_tickers = (sz["A股代码"].astype(str).str.zfill(6) + ".SZ").tolist()
        return sh_tickers + sz_tickers
    except Exception as e:
        print(f"[warn] akshare not available or error: {e}")
        # Fallback: a curated list of major China ETFs accessible via yfinance
        return [
            "000001.SS", "000002.SZ", "600519.SS", "601398.SS",
            "600036.SS", "000858.SZ", "000333.SZ", "002594.SZ",
        ]


# ── Combined universe ──────────────────────────────────────────────────────────

def build_universe(include_us: bool = True, include_china: bool = True) -> dict:
    universe = {}
    if include_us:
        us = get_us_universe()
        universe["US"] = us
        print(f"[universe] US: {len(us)} tickers")
    if include_china:
        cn = get_china_universe()
        universe["CN"] = cn
        print(f"[universe] China: {len(cn)} tickers")
    return universe


if __name__ == "__main__":
    u = build_universe()
    with open("universe.json", "w") as f:
        json.dump(u, f, indent=2)
    print("Saved universe.json")
