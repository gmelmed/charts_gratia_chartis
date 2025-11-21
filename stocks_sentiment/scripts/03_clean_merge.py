import sys
import os
from pathlib import Path
sys.path.append('.')

# Get the stocks_sentiment directory
STOCKS_DIR = Path(__file__).resolve().parent.parent
RAW_DATA_DIR = STOCKS_DIR / "data" / "raw"
PROCESSED_DATA_DIR = STOCKS_DIR / "data" / "processed"

# list of FRED series IDs to fetch
FRED_SERIES_IDS = [
    "UMCSENT",      # University of Michigan Consumer Sentiment Index
]

if __name__ == "__main__":
    import pandas as pd
    from importlib.util import spec_from_file_location, module_from_spec

    # Import get_fred_series
    module_path_candidates = [
        os.path.join(os.path.dirname(__file__), "_01_get_fred_series.py"),
        os.path.join(os.path.dirname(__file__), "01_get_fred_series.py"),
    ]
    spec = None
    for path in module_path_candidates:
        if os.path.isfile(path):
            spec = spec_from_file_location("get_fred_module", path)
            break
    if spec is None:
        raise ImportError(f"Could not find _01_get_fred_series.py or 01_get_fred_series.py in {os.path.dirname(__file__)}")
    module = module_from_spec(spec)
    spec.loader.exec_module(module)
    get_fred_series = module.get_fred_series

    # Fetch consumer sentiment data from FRED
    for series_id in FRED_SERIES_IDS:
        try:
            print(f"Fetching {series_id}...")
            get_fred_series(series_id, prompt_for_key=True)
        except Exception as e:
            print(f"Error fetching {series_id}: {e}")
    
    # Import get_monthly_stock_data
    yahoo_module_path_candidates = [
        os.path.join(os.path.dirname(__file__), "_02_get_yahoo_finance_data.py"),
        os.path.join(os.path.dirname(__file__), "02_get_yahoo_finance_data.py"),
    ]
    yahoo_spec = None
    for path in yahoo_module_path_candidates:
        if os.path.isfile(path):
            yahoo_spec = spec_from_file_location("yahoo_module", path)
            break
    if yahoo_spec is None:
        raise ImportError(f"Could not find _02_get_yahoo_finance_data.py or 02_get_yahoo_finance_data.py in {os.path.dirname(__file__)}")
    yahoo_module = module_from_spec(yahoo_spec)
    yahoo_spec.loader.exec_module(yahoo_module)
    get_monthly_stock_data = yahoo_module.get_monthly_stock_data
    
    # Fetch S&P 500 data from Yahoo Finance
    print("\nFetching stock data from Yahoo Finance...")
    sp500_df = get_monthly_stock_data(
        "^GSPC",  # S&P 500 ticker
        save_path=RAW_DATA_DIR / "GSPC.csv"
    )
    
    # Read the saved files
    sp500_df = pd.read_csv(RAW_DATA_DIR / "GSPC.csv", parse_dates=["date"])
    umcsent_df = pd.read_csv(RAW_DATA_DIR / "UMCSENT.csv", parse_dates=["date"])
    
    # Rename S&P 500 close column for clarity
    sp500_df = sp500_df[["date", "close"]].rename(columns={"close": "SP500"})
    
    # add recent values to umcsent_df
    umcsent_recent = pd.DataFrame({
        "date": pd.to_datetime(["2025-10-01", "2025-11-01"]),
        "UMCSENT": [53.6, 50.3]
    })
    umcsent_df = pd.concat([umcsent_df, umcsent_recent], ignore_index=True)
    
    # Merge on date
    merged_df = pd.merge(sp500_df, umcsent_df, on="date", how="inner")
    
    # Sort by date
    merged_df = merged_df.sort_values("date")
    
    # Calculate YoY changes
    merged_df["SP500_yoy_change"] = merged_df["SP500"].pct_change(periods=12) * 100
    merged_df["UMCSENT_yoy_change"] = merged_df["UMCSENT"].pct_change(periods=12) * 100
    
    # Calculate the difference (sentiment minus stock market)
    merged_df["yoy_change_diff"] = merged_df["UMCSENT_yoy_change"] - merged_df["SP500_yoy_change"]
    
    # Create processed directory if needed
    PROCESSED_DATA_DIR.mkdir(parents=True, exist_ok=True)
    
    # Save merged data
    output_path = PROCESSED_DATA_DIR / "merged_sp500_umcsent.csv"
    merged_df.to_csv(output_path, index=False)
    print(f"\nMerged data saved to {output_path}")
    print(f"Date range: {merged_df['date'].min()} to {merged_df['date'].max()}")
    print(f"Total months: {len(merged_df)}")