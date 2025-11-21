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
    # period="max" gets all available data
    ticker_obj = yf.Ticker(ticker)
    df = ticker_obj.history(period="max", interval="1mo", start=start_date, end=end_date)
    
    if df.empty:
        raise ValueError(f"No data returned for ticker {ticker}")
    
    # Reset index to have date as a column
    df.reset_index(inplace=True)
    
    # Rename Date to date (lowercase for consistency)
    df.rename(columns={'Date': 'date'}, inplace=True)
    
    # Convert date to datetime and keep only the date part
    df['date'] = pd.to_datetime(df['date']).dt.date
    df['date'] = pd.to_datetime(df['date'])
    
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