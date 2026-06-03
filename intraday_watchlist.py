"""
Intraday Watchlist
==================
Edit this file to add/remove tickers from the intraday scan.
Max ~50 tickers recommended for GitHub Actions runtime limits.

Groups are cosmetic — they only affect how tickers are labelled
in the output. You can rename or add groups freely.
"""

WATCHLIST: dict[str, list[str]] = {
    "ETF": [
        "SPY", "QQQ", "IWM", "DIA",
        "XLK", "XLF", "XLE", "XLV",
        "GLD", "TLT", "HYG",
    ],
    "Tech": [
        "AAPL", "MSFT", "NVDA", "GOOGL", "META", "AMZN",
        "TSLA", "AMD", "AVGO", "ORCL",
    ],
    "Finance": [
        "JPM", "BAC", "GS", "MS",
    ],
    "Other": [
        # Add any other US stocks/ETFs here
    ],
}


def build_intraday_universe() -> list[tuple[str, str]]:
    """
    Returns a flat list of (ticker, group) tuples.
    Deduplicates across groups — first occurrence wins.
    """
    seen = set()
    tasks = []
    for group, tickers in WATCHLIST.items():
        for t in tickers:
            t = t.upper().strip()
            if t and t not in seen:
                seen.add(t)
                tasks.append((t, group))
    return tasks
