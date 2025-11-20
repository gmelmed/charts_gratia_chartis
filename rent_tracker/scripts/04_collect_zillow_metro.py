"""Collect Zillow metro-level rent data."""

import pandas as pd

import sys
sys.path.append('.')

import config


def collect_zillow_metro_data():
    """Collect and process Zillow metro-level rent data."""
    print("Starting Zillow metro data collection...")
    
    # Read in the ZORI metro data
    print(f"  Fetching data from: {config.ZILLOW_METRO_URL}")
    zori_metro_wide = pd.read_csv(config.ZILLOW_METRO_URL)
    
    # Save raw data
    zori_metro_wide.to_csv(config.ZILLOW_METRO_RAW, index=False)
    
    print(f"\n✓ Zillow metro data collection complete!")
    print(f"  Metro areas: {len(zori_metro_wide)}")
    print(f"  Saved to: {config.ZILLOW_METRO_RAW}")


if __name__ == "__main__":
    collect_zillow_metro_data()