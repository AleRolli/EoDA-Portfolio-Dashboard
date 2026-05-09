# Project: Asset Management Data Pipeline    
         
    ## Context    
    This is Assignment 2 for "Engineering of Data Analysis" at NOVA SBE.    
    We're building an end-to-end medallion data pipeline on Databricks Free Edition.    
         
    ## Architecture    
    - Bronze: raw OHLCV data from yfinance, append-only, in /Volumes/asset_mgmt/bronze/prices/    
    - Silver: silver.daily_prices Delta table, deduplicated, validated    
    - Gold: gold.dashboard_latest_prices and gold.ticker_performance    
         
    ## Conventions    
    - Catalog: asset_mgmt    
    - Schemas: bronze, silver, gold    
    - Notebook prefixes: 00_live_pull, 01_bronze_ingest, 02_silver_build, 03_gold_build    
    - Use Delta MERGE INTO for incremental updates (never full overwrites)    
    - Every Gold column needs a COMMENT string for Genie    
    - Hybrid ingestion: static batches + live yfinance scheduled pull    
         
    ## Ticker universe    
    25 S&P 500 stocks across Tech, Finance, Healthcare, Energy, Consumer + SPY.    
         
    ## Files    
    - scripts/prepare_data.py: local script to pull historical data    
    - notebooks/*.ipynb: Databricks notebooks (PySpark + SQL)    
    - data/: batch files (gitignored)    
         
    ## Deadline    
    16 May 2026, 23:59 Lisbon time.
