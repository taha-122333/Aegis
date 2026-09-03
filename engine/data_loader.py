"""
Downloads historical daily price data for the Aegis asset universe and
caches it locally as a Parquet file, so we don't hit the data source
every time we run something.
"""

import time

import pandas as pd
import yfinance as yf

from engine.config import TICKERS, START_DATE, END_DATE, PRICES_FILE, DATA_DIR


def _download_single(ticker: str, start, end, retries: int = 3, delay: float = 2.0) -> pd.Series:
    """
    Downloads one ticker with a few retries, since yfinance occasionally
    fails a single ticker in a batch call for no real reason (rate limiting,
    a dropped request, etc.). Returns an all-NaN series if every attempt fails.
    """
    for attempt in range(1, retries + 1):
        data = yf.download(ticker, start=start, end=end, auto_adjust=True, progress=False)
        if not data.empty and "Close" in data:
            return data["Close"]
        time.sleep(delay)
    print(f"WARNING: could not download {ticker} after {retries} attempts — filled with NaN")
    return pd.Series(dtype=float, name=ticker)


def download_prices(tickers=TICKERS, start=START_DATE, end=END_DATE) -> pd.DataFrame:
    """
    Downloads adjusted close prices for a list of tickers from Yahoo Finance
    and returns them as a single DataFrame: one column per ticker, one row
    per trading day. Any ticker that fails the bulk download is retried
    individually so one bad ticker doesn't blank out its whole column.
    """
    raw = yf.download(tickers, start=start, end=end, auto_adjust=True, progress=False)
    prices = raw["Close"]

    failed = [t for t in tickers if t not in prices.columns or prices[t].isna().all()]
    for ticker in failed:
        print(f"Retrying {ticker} individually...")
        prices[ticker] = _download_single(ticker, start, end)

    prices = prices.dropna(how="all")
    return prices


def save_prices(prices: pd.DataFrame, path=PRICES_FILE) -> None:
    """Saves a prices DataFrame to disk as Parquet."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    prices.to_parquet(path)


def load_prices(path=PRICES_FILE) -> pd.DataFrame:
    """Loads cached prices from disk. Raises if the cache doesn't exist yet."""
    if not path.exists():
        raise FileNotFoundError(
            f"No cached price data at {path}. Run download_prices() and "
            f"save_prices() first."
        )
    return pd.read_parquet(path)


def get_prices(refresh: bool = False) -> pd.DataFrame:
    """
    Main entry point: returns price data, downloading fresh data only if
    refresh=True or no cache exists yet.
    """
    if refresh or not PRICES_FILE.exists():
        prices = download_prices()
        save_prices(prices)
        return prices
    return load_prices()


if __name__ == "__main__":
    prices = get_prices(refresh=True)
    print(prices.tail())
    print(f"\nDownloaded {prices.shape[0]} days x {prices.shape[1]} assets")
    print(f"NaN count per ticker:\n{prices.isna().sum()}")