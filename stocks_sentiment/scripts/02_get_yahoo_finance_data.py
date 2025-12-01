import pandas as pd
from pathlib import Path
import yfinance as yf

def get_monthly_stock_data(ticker, start_date=None, end_date=None, save_path=None):
    """
    Fetch monthly stock data for a given ticker from Yahoo Finance
    and save it as a CSV file.

    If start_date or end_date are None, yfinance will use the earliest/latest available dates.
    """
    sd_text = start_date if start_date is not None else "earliest available"
    ed_text = end_date if end_date is not None else "latest available"
    print(f"Fetching data for {ticker} from {sd_text} to {ed_text}...")
    
    # Download historical data
    # Use daily data and resample to get the last day of each month
    ticker_obj = yf.Ticker(ticker)
    df = ticker_obj.history(period="max", interval="1d", start=start_date, end=end_date)

    if df.empty:
        raise ValueError(f"No data returned for ticker {ticker}")

    # Reset index to have date as a column
    df.reset_index(inplace=True)

    # Rename Date to date (lowercase for consistency)
    df.rename(columns={'Date': 'date'}, inplace=True)

    # Convert date to datetime
    df['date'] = pd.to_datetime(df['date'])

    # Set date as index for resampling
    df.set_index('date', inplace=True)

    # Resample to monthly frequency, taking the last value of each month
    df = df.resample('ME').last()

    # Reset index to have date as a column again
    df.reset_index(inplace=True)
    
    # Keep only relevant columns and lowercase them
    df.columns = df.columns.str.lower()
    df = df[['date', 'open', 'high', 'low', 'close', 'volume']]
    
    # Ensure the save directory exists if a path was provided
    if save_path:
        Path(save_path).parent.mkdir(parents=True, exist_ok=True)
        df.to_csv(save_path, index=False)
        print(f"Data for {ticker} saved to {save_path}.")
        print(f"  Date range: {df['date'].min()} to {df['date'].max()}")
        print(f"  Total months: {len(df)}")
        return df
    else:
        print("No save_path provided; returning DataFrame.")
        return df