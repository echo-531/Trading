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
        "SPY", "QQQ", "IWM",
        "XLK", "XLF", "XLE",
        "GLD", 
    ],
    
    "Tech": [
        "MXL", "ARM", "ALAB", "SIMO", "GFS", "JBL", "FLEX",
        "STX", "FORM", "ANET", "VICR", 
        "CLS", "SHOP", "SYM", "OUST", "XE", "AMPX", "INOD", "PLTR", 
        "FLY", "CRCL", "AMD", "AVGO", "ORCL",
    ],
    
    "光": [
        "POET", "OCS", "GLW", "COHR", "LITE", "VELO", "AAOI", "CIEN", 
    ],
    
    "MEGA7": [
        "META", "AAPL", "NVDA", "MSFT", "TSLA", "AMZN", "GOOGL",
    ],
    
    "存储": [
        "SNDK", "WDC", "MRVL", "MU",
    ],
    
    "太空": [
        "RKLB", "PL", "ONDS", 
    ],

    "数据中心": [
        "NBIS", "IREN",
    ],

    "电力": [
        "VRT", "BE", 
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
