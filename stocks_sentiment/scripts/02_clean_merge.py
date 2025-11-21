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
    "SP500",        # S&P 500 Index
    "DJIA",         # Dow Jones Industrial Average
    "NASDAQCOM",    # NASDAQ Composite Index
]

if __name__ == "__main__":
    from importlib.util import spec_from_file_location, module_from_spec

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

    for series_id in FRED_SERIES_IDS:
        try:
            print(f"Fetching {series_id}...")
            get_fred_series(series_id, prompt_for_key=True)
        except Exception as e:
            print(f"Error fetching {series_id}: {e}")
            
    # merge nasdaq and umcsent data
    import pandas as pd
    
    # Use absolute paths
    nasdaq_df = pd.read_csv(RAW_DATA_DIR / "NASDAQCOM.csv", parse_dates=["date"])
    umcsent_df = pd.read_csv(RAW_DATA_DIR / "UMCSENT.csv", parse_dates=["date"])
    merged_df = pd.merge(nasdaq_df, umcsent_df, on="date", how="inner")
    
    # get yoy change for both series
    merged_df["NASDAQCOM_yoy_change"] = merged_df["NASDAQCOM"].pct_change(periods=12) * 100
    merged_df["UMCSENT_yoy_change"] = merged_df["UMCSENT"].pct_change(periods=12) * 100
    
    # record the difference between the two yoy changes
    merged_df["yoy_change_diff"] = merged_df["UMCSENT_yoy_change"] - merged_df["NASDAQCOM_yoy_change"]
    
    # Create processed directory if needed
    PROCESSED_DATA_DIR.mkdir(parents=True, exist_ok=True)
    
    # save merged data
    output_path = PROCESSED_DATA_DIR / "merged_nasdaq_umcsent.csv"
    merged_df.to_csv(output_path, index=False)
    print(f"Merged data saved to {output_path}")