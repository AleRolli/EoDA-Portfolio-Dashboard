"""
Pull 22 months of daily OHLCV data from yfinance, split into seed (months 1-21)
and batch_2 (month 22), and save as Parquet files.
"""

import sys
from pathlib import Path
from dateutil.relativedelta import relativedelta
from datetime import date

import pandas as pd
import yfinance as yf

# ---------------------------------------------------------------------------
# Ticker universe: 25 S&P 500 stocks across 5 sectors + SPY benchmark
# ---------------------------------------------------------------------------
TICKERS = [
    # Tech
    "AAPL", "MSFT", "NVDA", "GOOGL", "META",
    # Finance
    "JPM", "BAC", "GS", "MS", "WFC",
    # Healthcare
    "JNJ", "UNH", "PFE", "ABBV", "MRK",
    # Energy
    "XOM", "CVX", "COP", "SLB", "EOG",
    # Consumer
    "AMZN", "HD", "MCD", "NKE", "COST",
    # Benchmark
    "SPY",
]

# ---------------------------------------------------------------------------
# Date range
# ---------------------------------------------------------------------------
TODAY = date.today()
START_DATE = TODAY - relativedelta(months=22)
SPLIT_DATE = TODAY - relativedelta(months=1)   # first day of month 22

SEED_DIR = Path(__file__).parent.parent / "data" / "seed"
BATCH2_DIR = Path(__file__).parent.parent / "data" / "batch_2"


def pull_ticker(ticker: str, start: date, end: date) -> pd.DataFrame | None:
    try:
        df = yf.download(
            ticker,
            start=start.isoformat(),
            end=end.isoformat(),
            auto_adjust=True,
            progress=False,
        )
        if df.empty:
            print(f"  [WARN] {ticker}: no data returned — skipping")
            return None

        df = df[["Open", "High", "Low", "Close", "Volume"]].copy()
        df.index.name = "Date"
        df.reset_index(inplace=True)
        df.insert(0, "Ticker", ticker)
        return df

    except Exception as exc:
        print(f"  [ERROR] {ticker}: {exc} — skipping")
        return None


def main() -> None:
    print(f"Date range : {START_DATE}  →  {TODAY}")
    print(f"Seed       : {START_DATE}  →  {SPLIT_DATE - relativedelta(days=1)}")
    print(f"Batch_2    : {SPLIT_DATE}  →  {TODAY}")
    print(f"Tickers    : {len(TICKERS)}\n")

    frames: list[pd.DataFrame] = []
    failed: list[str] = []

    for ticker in TICKERS:
        print(f"  Pulling {ticker} ...", end=" ", flush=True)
        df = pull_ticker(ticker, START_DATE, TODAY)
        if df is not None:
            frames.append(df)
            print(f"{len(df)} rows")
        else:
            failed.append(ticker)

    if not frames:
        print("\n[FATAL] No data pulled. Check your internet connection.")
        sys.exit(1)

    all_data = pd.concat(frames, ignore_index=True)
    all_data["Date"] = pd.to_datetime(all_data["Date"])

    seed = all_data[all_data["Date"] < pd.Timestamp(SPLIT_DATE)].reset_index(drop=True)
    batch2 = all_data[all_data["Date"] >= pd.Timestamp(SPLIT_DATE)].reset_index(drop=True)

    SEED_DIR.mkdir(parents=True, exist_ok=True)
    BATCH2_DIR.mkdir(parents=True, exist_ok=True)

    seed_path = SEED_DIR / "ohlcv_seed.parquet"
    batch2_path = BATCH2_DIR / "ohlcv_batch_2.parquet"

    seed.to_parquet(seed_path, index=False)
    batch2.to_parquet(batch2_path, index=False)

    print(f"\nSeed       → {seed_path}  ({len(seed):,} rows, {seed['Ticker'].nunique()} tickers)")
    print(f"Batch_2    → {batch2_path}  ({len(batch2):,} rows, {batch2['Ticker'].nunique()} tickers)")

    if failed:
        print(f"\n[WARN] Failed tickers ({len(failed)}): {', '.join(failed)}")


if __name__ == "__main__":
    main()
