"""
Central configuration for Aegis: which assets we track, over what date
range, and where data files live on disk.
"""

from pathlib import Path

# Root of the project on disk (this file's parent's parent = aegis/)
PROJECT_ROOT = Path(__file__).resolve().parent.parent

# Where downloaded price data is cached
DATA_DIR = PROJECT_ROOT / "data"
PRICES_FILE = DATA_DIR / "prices.parquet"

# Starting asset universe: a few large-cap stocks, an index ETF, gold, crypto
TICKERS = [
    "AAPL",     # Apple - large-cap stock
    "MSFT",     # Microsoft - large-cap stock
    "NVDA",     # Nvidia - large-cap stock
    "SPY",      # S&P 500 index ETF
    "GLD",      # Gold ETF
    "BTC-USD",  # Bitcoin
    "ETH-USD",  # Ethereum
]

# How far back to pull daily price history
START_DATE = "2015-01-01"
END_DATE = None  # None = up to today

# Backtest parameters (Sprint 4)
BACKTEST_LOOKBACK_DAYS = 756          # ~3 years of trailing daily data used to estimate weights at each rebalance
BACKTEST_REBALANCE_FREQ = "M"         # "M" = monthly, "Q" = quarterly
BACKTEST_TRANSACTION_COST_BPS = 10.0  # 0.10% cost per unit of portfolio turnover