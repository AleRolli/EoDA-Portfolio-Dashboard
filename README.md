# Asset Management Data Pipeline
**Assignment 2 — Engineering of Data Analysis | NOVA SBE**

End-to-end medallion data pipeline built on Databricks Free Edition. Ingests 22+ months of daily OHLCV data for 26 S&P 500 tickers across 5 sectors, processes it through Bronze → Silver → Gold layers, and exposes it to Databricks Genie for natural-language querying.

---

## Architecture

```
yfinance (local)          yfinance (Databricks, daily 22:30 CET)
      │                               │
      ▼                               ▼
data/seed/                 Bronze uploads Volume
data/batch_2/    ─────►   /Volumes/asset_mgmt/bronze/uploads/
                                      │
                           01_bronze_ingest.ipynb
                                      │
                                      ▼
                           /Volumes/asset_mgmt/bronze/prices/
                           (append-only Parquet, partitioned by ingest_date)
                                      │
                           02_silver_build.ipynb
                                      │
                                      ▼
                           asset_mgmt.silver.daily_prices (Delta)
                           deduplicated · validated · enriched
                                      │
                           03_gold_build.ipynb
                                      │
                                      ▼
                  ┌───────────────────┴───────────────────┐
                  ▼                                       ▼
     gold.dashboard_latest_prices             gold.ticker_performance
     (one row per ticker, latest)          (one row per ticker per date)
```

---

## Ticker Universe

26 tickers across 5 sectors + benchmark:

| Sector | Tickers |
|---|---|
| Tech | AAPL · MSFT · NVDA · GOOGL · META |
| Finance | JPM · BAC · GS · MS · WFC |
| Healthcare | JNJ · UNH · PFE · ABBV · MRK |
| Energy | XOM · CVX · COP · SLB · EOG |
| Consumer | AMZN · HD · MCD · NKE · COST |
| Benchmark | SPY |

---

## Repo Structure

```
├── data/
│   ├── seed/                    ← months 1-21 (gitignored, share via OneDrive)
│   ├── batch_2/                 ← month 22   (gitignored, share via OneDrive)
│   └── frozen_live_snapshot/    ← captured at submission (gitignored)
├── notebooks/
│   ├── 00_live_pull.ipynb       ← daily yfinance pull (scheduled 22:30 CET)
│   ├── 01_bronze_ingest.ipynb   ← uploads → bronze/prices
│   ├── 02_silver_build.ipynb    ← bronze → silver.daily_prices (Delta)
│   └── 03_gold_build.ipynb      ← silver → gold tables (Delta)
├── scripts/
│   └── prepare_data.py          ← local script: pull 22 months, split seed/batch_2
├── report/
├── CLAUDE.md                    ← project context for Claude Code
└── README.md
```

---

## Local Setup

**Requirements:** Python 3.10+, Git

```bash
# 1. Clone the repo
git clone <your-github-repo-url>
cd EoDA-Portfolio-Dashboard

# 2. Create and activate virtual environment
python -m venv .venv
.venv\Scripts\activate          # Windows
# source .venv/bin/activate     # macOS/Linux

# 3. Install dependencies
pip install yfinance pandas pyarrow python-dateutil

# 4. Pull historical data (generates seed and batch_2 Parquet files)
python scripts/prepare_data.py
```

The script prints a summary when done:
```
Seed    → data/seed/ohlcv_seed.parquet     (≈27,000 rows, 26 tickers)
Batch_2 → data/batch_2/ohlcv_batch_2.parquet
```

> Data files are gitignored — share them via OneDrive for submission.

---

## Databricks Setup

### 1. Create catalog, schemas, and volumes

Run in a SQL notebook:

```sql
CREATE CATALOG IF NOT EXISTS asset_mgmt;
USE CATALOG asset_mgmt;

CREATE SCHEMA IF NOT EXISTS bronze;
CREATE SCHEMA IF NOT EXISTS silver;
CREATE SCHEMA IF NOT EXISTS gold;

CREATE VOLUME IF NOT EXISTS asset_mgmt.bronze.uploads;
CREATE VOLUME IF NOT EXISTS asset_mgmt.bronze.prices;
```

### 2. Upload data files

**Catalog → asset_mgmt → bronze → volumes → uploads → Upload to this volume**

Upload one file at a time, deleting the previous one before each run:
1. `data/seed/ohlcv_seed.parquet`
2. `data/batch_2/ohlcv_batch_2.parquet`

### 3. Import notebooks

**Workspace → Import** → select each `.ipynb` file from the `notebooks/` folder.

---

## Running the Pipeline

Run notebooks in order. Each is idempotent — safe to re-run.

### Bronze — `01_bronze_ingest.ipynb`

Run once per data file. Set the `source_type` widget before each run:

| Run | Widget: `source_type` | File in uploads |
|---|---|---|
| 1 | `seed` | `ohlcv_seed.parquet` |
| 2 | `batch_2` | `ohlcv_batch_2.parquet` |
| 3+ | `live` | `live_YYYY-MM-DD.parquet` (auto-generated) |

### Live pull — `00_live_pull.ipynb`

Runs automatically via Databricks Jobs at **22:30 CET / Europe/Paris** every day.
No-op on weekends and market holidays (clean exit, no error).

To set up the job: **Workflows → Create job** → Notebook task → cron `30 22 * * *` → timezone `Europe/Paris`.

After the job fires, run `01_bronze_ingest` with `source_type=live` to push it into Bronze.

### Silver — `02_silver_build.ipynb`

Reads all Bronze data, applies cleaning and enrichment, merges into `silver.daily_prices`.

Run after every Bronze ingest. MERGE INTO ensures no duplicates.

### Gold — `03_gold_build.ipynb`

Builds `gold.dashboard_latest_prices` and `gold.ticker_performance` from Silver.

Run after Silver. All columns have COMMENT strings for Genie compatibility.

---

## Databricks Conventions

- Catalog: `asset_mgmt`
- Schemas: `bronze` · `silver` · `gold`
- All Silver/Gold updates use `MERGE INTO` — never full overwrites
- Every Gold column has a `COMMENT` string for Genie

---

## Deadline

**16 May 2026, 23:59 Lisbon time**
