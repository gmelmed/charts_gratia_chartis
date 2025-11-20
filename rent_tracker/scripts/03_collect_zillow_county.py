"""Collect Zillow county-level rent data."""

import pandas as pd

import sys
sys.path.append('.')

import config


def collect_zillow_county_data():
    """Collect and process Zillow county-level rent data."""
    print("Starting Zillow county data collection...")
    
    # Read in the ZORI county wide data
    print(f"  Fetching data from: {config.ZILLOW_COUNTY_URL}")
    zori_county_wide = pd.read_csv(config.ZILLOW_COUNTY_URL)
    
    # Clean
    zori_county_wide.drop(columns=['RegionID', 'SizeRank', 'RegionType', 
                                    'StateName', 'Metro'], inplace=True)
    
    # Calculate fips
    zori_county_wide['fips'] = (zori_county_wide['StateCodeFIPS'] * 1000 + 
                                 zori_county_wide['MunicipalCodeFIPS'])
    
    # Drop state and municipal code fips
    zori_county_wide.drop(columns=['StateCodeFIPS', 'MunicipalCodeFIPS'], inplace=True)
    
    # Create region name
    zori_county_wide['region_name'] = (zori_county_wide['RegionName'] + ", " + 
                                        zori_county_wide['State'])
    
    # Drop region name and state columns
    zori_county_wide.drop(columns=['RegionName', 'State'], inplace=True)
    
    # Save raw data
    zori_county_wide.to_csv(config.ZILLOW_COUNTY_RAW, index=False)
    
    print(f"\n✓ Zillow county data collection complete!")
    print(f"  Counties: {len(zori_county_wide)}")
    print(f"  Saved to: {config.ZILLOW_COUNTY_RAW}")


if __name__ == "__main__":
    collect_zillow_county_data()