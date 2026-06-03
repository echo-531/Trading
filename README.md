# MRMC Signal Scanner

Scans US stocks (price > $20) and Chinese A-shares for **抄底** (buy) and **卖出** (sell) signals
using a faithful bar-by-bar Python implementation of the MooMoo MRMC indicator.

## Project structure

```
mrmc_scanner/
├── scanner/
│   ├── engine.py       ← MooMoo formula primitives (EMA, REF, BARSLAST, HHV, LLV, COUNT)
│   ├── indicator.py    ← Line-by-line translation of the MRMC formula
│   ├── universe.py     ← Builds US + China ticker lists
│   ├── fetcher.py      ← Downloads forward-adjusted OHLCV via yfinance
│   └── scanner.py      ← Main scan loop → signals.json
├── docs/
│   ├── index.html      ← Dashboard (hosted on GitHub Pages)
│   └── signals.json    ← Latest scan results (auto-updated by CI)
├── .github/workflows/
│   └── scan.yml        ← GitHub Actions: daily cron after market close
└── requirements.txt
```

## Setup (one-time)

### 1. Create a GitHub repository

```bash
git init mrmc_scanner
cd mrmc_scanner
git remote add origin https://github.com/YOUR_USERNAME/mrmc_scanner.git
```

### 2. Copy all files into the repo

Place `engine.py`, `indicator.py`, `universe.py`, `fetcher.py`, `scanner.py`, `requirements.txt`
inside a `scanner/` subfolder. Place `docs/` at the root.

### 3. Enable GitHub Pages

In your repo → **Settings → Pages → Source → Deploy from branch → main → /docs**.

Your dashboard will be live at: `https://YOUR_USERNAME.github.io/mrmc_scanner/`

### 4. Enable GitHub Actions

The workflow file at `.github/workflows/scan.yml` runs automatically every weekday at 23:00 UTC
(after US market close). It:

1. Installs Python dependencies
2. Runs `scanner.py`
3. Copies `signals.json` → `docs/signals.json`
4. Commits and pushes the update

**No server or paid infrastructure needed.**

### 5. Test locally first

```bash
cd scanner
pip install -r ../requirements.txt

# Quick test — first 50 S&P 500 stocks, daily only
python scanner.py --quick

# Debug a single ticker
python scanner.py --ticker AAPL

# Full scan (takes ~30-60 min)
python scanner.py
```

## How signals work

| Signal | Chinese | Meaning |
|--------|---------|---------|
| `buy_signal = 1` | 抄底 | Multi-cycle MACD bullish divergence: price lower lows + MACD higher lows |
| `sell_signal = 1` | 卖出 | Multi-cycle MACD bearish divergence: price higher highs + MACD lower highs |

Signals are computed on **forward-adjusted prices** across three timeframes:
- **Daily** (`1d`) — short-term signals
- **Weekly** (`1wk`) — medium-term signals  
- **Monthly** (`1mo`) — long-term signals

## Indicator parameters (MooMoo defaults)

| Param | Default | Meaning |
|-------|---------|---------|
| `S`   | 12      | Fast EMA period |
| `P`   | 26      | Slow EMA period |
| `M`   | 9       | Signal EMA period |

To change: edit the `run_mrmc(df, S=12, P=26, M=9)` call in `scanner.py`.

## Universe

- **US**: S&P 500 + Nasdaq 100, filtered to price > $20
- **China**: All Shanghai (`.SS`) + Shenzhen (`.SZ`) A-shares via `akshare`

## Troubleshooting

**`akshare` not available**: The scanner falls back to a small list of major Chinese tickers.
Install akshare: `pip install akshare`

**Rate limits from yfinance**: The scanner sleeps 150ms between tickers. Increase
`time.sleep(0.15)` in `scanner.py` if you hit rate limits.

**GitHub Actions quota**: Free GitHub accounts get 2,000 minutes/month. A full scan takes
~40-60 min, so daily runs use ~1,200 min/month — within the free tier.
