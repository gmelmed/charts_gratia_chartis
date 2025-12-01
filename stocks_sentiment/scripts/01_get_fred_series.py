import os
import requests
import pandas as pd
from pathlib import Path

def get_fred_series(series_id, api_key=None, save_dir=None, prompt_for_key=False):
    """
    Fetch a FRED series and return a DataFrame with columns: date, <series_id>.
    Saves CSV named "<series_id>.csv" in save_dir (defaults to stocks_sentiment/data/raw).
    Resamples to last day of month and fetches maximum available history.
    """
    # resolve paths relative to this script
    script_dir = Path(__file__).resolve().parent
    stocks_dir = script_dir.parent
    key_file = stocks_dir / "FRED_api_key.txt"

    # obtain API key
    API_KEY = api_key
    if not API_KEY:
        if key_file.exists():
            API_KEY = key_file.read_text(encoding="utf-8").strip()
        else:
            API_KEY = os.environ.get("FRED_API_KEY")

    if not API_KEY and prompt_for_key:
        API_KEY = input("Enter your FRED API key: ").strip()

    if not API_KEY:
        raise ValueError("FRED API key required. Provide api_key, set FRED_API_KEY env var, or place it in FRED_api_key.txt.")

    # call FRED - remove observation_start to get all available data
    url = "https://api.stlouisfed.org/fred/series/observations"
    params = {
        "series_id": series_id, 
        "api_key": API_KEY, 
        "file_type": "json"
        # No observation_start parameter = get all available data
    }
    resp = requests.get(url, params=params)
    resp.raise_for_status()
    obs = resp.json().get("observations", [])

    df = pd.DataFrame(obs)
    if df.empty:
        raise RuntimeError(f"No observations returned for {series_id}.")

    # prepare dataframe
    df = df.set_index("date")
    df.index = pd.to_datetime(df.index)
    df["value"] = pd.to_numeric(df["value"], errors="coerce")

    # Resample to last day of month, taking the last available value
    df_monthly = df[["value"]].resample('ME').last()

    # Drop any rows with NaN values
    df_monthly = df_monthly.dropna()
    
    out = df_monthly.rename(columns={"value": series_id}).reset_index()
    out = out.rename(columns={"date": "date"})

    # save CSV
    if save_dir is None:
        save_dir = stocks_dir / "data" / "raw"
    save_dir = Path(save_dir)
    save_dir.mkdir(parents=True, exist_ok=True)
    output_path = save_dir / f"{series_id}.csv"
    out.to_csv(output_path, index=False)
    print(f"{series_id} data saved to: {output_path}")
    print(f"  Date range: {out['date'].min()} to {out['date'].max()}")
    print(f"  Total months: {len(out)}")

    return out