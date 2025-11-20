"""Merge all datasets and create final processed outputs."""

import pandas as pd
import json

import sys
sys.path.append('.')

import config


def process_homebuilding_data(homebuilding_raw, metros_pop, top_metros):
    """Process homebuilding data with population adjustments."""
    print("  Processing homebuilding data...")
    
    homebuilding = homebuilding_raw.copy()
    
    # Lowercase columns
    homebuilding.columns = homebuilding.columns.str.lower()
    
    # Ensure the DataFrame is sorted by 'name' and 'date'
    homebuilding = homebuilding.sort_values(by=['name', 'date'])
    
    # Create a 12-month running total column
    homebuilding['rt'] = (
        homebuilding.groupby('name')['total']
        .rolling(window=12, min_periods=1)
        .sum()
        .reset_index(level=0, drop=True)
    )
    
    # Create a 12-month running total column for multi-unit structures
    homebuilding['multi_rt'] = (
        homebuilding.groupby('name')['multi_total']
        .rolling(window=12, min_periods=1)
        .sum()
        .reset_index(level=0, drop=True)
    )
    
    # CHANGED: Keep the original columns plus the running totals
    homebuilding = homebuilding[['name', 'date', 'total', '1 unit', '2 units', 
                                  '3 and 4 units', '5 units or more', 'multi_total',
                                  'rt', 'multi_rt']]
    
    # Merge with population data
    homebuilding = pd.merge(homebuilding, metros_pop, on='name', how='inner')
    
    # Calculate per capita metrics (per 1000 people)
    homebuilding['rt_pc'] = (homebuilding['rt'] / homebuilding['population']) * 1000
    homebuilding['multi_rt_pc'] = (homebuilding['multi_rt'] / homebuilding['population']) * 1000
    
    # Add region
    homebuilding['region'] = homebuilding['name'].map(config.REGION_MAP)
    
    # Save processed homebuilding data
    homebuilding.to_csv(config.HOMEBUILDING_CLEAN, index=False)
    print(f"    ✓ Saved to: {config.HOMEBUILDING_CLEAN}")
    
    return homebuilding

def process_zillow_county_data(zori_county_wide):
    """Process Zillow county data to calculate changes."""
    print("  Processing Zillow county data...")
    
    # Get date columns
    date_cols = [col for col in zori_county_wide.columns if col not in ['fips', 'region_name']]
    date_cols_dt = pd.to_datetime(date_cols)
    
    most_recent_date = date_cols_dt.max()
    most_recent_col = most_recent_date.strftime('%Y-%m-%d')
    
    # Calculate one-year and five-year changes
    one_year_date = most_recent_date - pd.DateOffset(years=1)
    five_year_date = most_recent_date - pd.DateOffset(years=5)
    
    # Find the closest matching columns for these dates
    one_year_col = min(date_cols, key=lambda x: abs(pd.to_datetime(x) - one_year_date))
    five_year_col = min(date_cols, key=lambda x: abs(pd.to_datetime(x) - five_year_date))
    
    # Create the new dataframe
    zori_county_clean = pd.DataFrame({
        'region_name': zori_county_wide['region_name'],
        'fips': zori_county_wide['fips'],
        'most_recent_date': most_recent_date,
        'most_recent_value': zori_county_wide[most_recent_col],
        'one_year_date': pd.to_datetime(one_year_col),
        'one_year_value': zori_county_wide[one_year_col],
        'one_year_change': ((zori_county_wide[most_recent_col] - zori_county_wide[one_year_col]) / 
                            zori_county_wide[one_year_col] * 100),
        'five_year_date': pd.to_datetime(five_year_col),
        'five_year_value': zori_county_wide[five_year_col],
        'five_year_change': ((zori_county_wide[most_recent_col] - zori_county_wide[five_year_col]) / 
                             zori_county_wide[five_year_col] * 100)
    })
    
    # Ensure proper data types
    zori_county_clean['fips'] = zori_county_clean['fips'].astype(int)
    zori_county_clean['region_name'] = zori_county_clean['region_name'].astype(str)
    
    # Save to csv
    zori_county_clean.to_csv(config.ZORI_COUNTY_CLEAN, index=False)
    print(f"    ✓ Saved to: {config.ZORI_COUNTY_CLEAN}")
    
    return zori_county_clean


def process_zillow_metro_data(zori_metro_wide, cities, metros_pop, top_metros):
    """Process Zillow metro data into long format with changes."""
    print("  Processing Zillow metro data...")
    
    index_cols = ['RegionID', 'SizeRank', 'RegionName', 'RegionType', 'StateName']
    
    # Melt df
    zori_metro_long = pd.melt(
        zori_metro_wide,
        id_vars=index_cols,
        value_vars=[col for col in zori_metro_wide.columns if col not in index_cols],
        var_name="date",
        value_name="zori"
    )
    
    zori_metro_long['date'] = pd.to_datetime(zori_metro_long['date'])
    
    # Increase date by one day
    zori_metro_long['date'] += pd.Timedelta(days=1)
    
    zori_metro_long = zori_metro_long[['RegionName', 'date', 'zori']]
    zori_metro_long.rename(columns={'RegionName': 'name'}, inplace=True)
    
    # Merge with cities to get lat/lon/population
    zori_metro_long = pd.merge(zori_metro_long, cities, on='name', how='left')
    
    # Calculate 1-year and 5-year changes
    zori_metro_long = zori_metro_long.sort_values(by=['name', 'date'])
    zori_metro_long['one_year_change'] = (zori_metro_long.groupby('name')['zori']
                                           .pct_change(periods=12, fill_method=None) * 100)
    zori_metro_long['five_year_change'] = (zori_metro_long.groupby('name')['zori']
                                            .pct_change(periods=60, fill_method=None) * 100)
    
    # Save the date of one year and five year comparisons
    zori_metro_long['one_year_date'] = zori_metro_long['date'] - pd.DateOffset(years=1)
    zori_metro_long['five_year_date'] = zori_metro_long['date'] - pd.DateOffset(years=5)
    
    # Filter to top metros
    zori_metro_long = zori_metro_long[zori_metro_long['name'].isin(top_metros)]
    
    # Save long format data
    zori_metro_long.to_csv(config.ZORI_METRO_LONG, index=False)
    print(f"    ✓ Saved to: {config.ZORI_METRO_LONG}")
    
    # Merge with metros_pop
    zori_metro_long = pd.merge(zori_metro_long, metros_pop, on='name', how='left')
    
    return zori_metro_long

def create_homebuilding_most_recent_all(homebuilding_raw_all, metros_pop, cities):
    """Create most recent homebuilding data for ALL metro areas (not just top 50)."""
    print("  Creating most recent homebuilding dataset for all metros...")
    
    homebuilding_all = homebuilding_raw_all.copy()
    
    # Calculate multi-unit total
    homebuilding_all['multi_total'] = (homebuilding_all['2 Units'] + 
                                        homebuilding_all['3 and 4 Units'] + 
                                        homebuilding_all['5 Units or More'])
    
    # Lowercase columns
    homebuilding_all.columns = homebuilding_all.columns.str.lower()
    
    # Get most recent date
    most_recent_date = homebuilding_all['date'].max()
    homebuilding_all = homebuilding_all[homebuilding_all['date'] == most_recent_date]
    
    # Merge with population data
    homebuilding_all = pd.merge(homebuilding_all, metros_pop, on='name', how='left')
    
    # Merge with cities for lat/lng
    homebuilding_all = pd.merge(homebuilding_all, cities[['name', 'lat', 'lng']], 
                                  on='name', how='left')
    
    # Add region
    homebuilding_all['region'] = homebuilding_all['name'].map(config.REGION_MAP)
    
    # Select final columns
    homebuilding_all = homebuilding_all[['name', 'date', 'total', '1 unit', '2 units', 
                                          '3 and 4 units', '5 units or more', 'multi_total',
                                          'population', 'lat', 'lng', 'region']]
    
    # Save
    homebuilding_all.to_csv(config.HOMEBUILDING_MOST_RECENT_ALL, index=False)
    print(f"    ✓ Saved to: {config.HOMEBUILDING_MOST_RECENT_ALL}")
    print(f"      Rows: {len(homebuilding_all)}, Metros: {homebuilding_all['name'].nunique()}")
    print(f"      Date: {most_recent_date}")
    
    return homebuilding_all

def create_final_merged_datasets(zori_metro_long, homebuilding):
    """Create final merged datasets with most recent data."""
    print("  Creating final merged datasets...")
    
    # Ensure date columns are the same type for merging
    zori_metro_long['date'] = pd.to_datetime(zori_metro_long['date'])
    homebuilding['date'] = pd.to_datetime(homebuilding['date'])
    
    # Get most recent dates
    most_recent_date = zori_metro_long['date'].max()
    most_recent_homebuilding_date = homebuilding['date'].max()
    
    # Create most recent datasets
    zori_metro_most_recent = zori_metro_long[zori_metro_long['date'] == most_recent_date].copy()
    zori_metro_building_most_recent = zori_metro_long[zori_metro_long['date'] == most_recent_homebuilding_date].copy()
    
    # Filter homebuilding to just the most recent date for each merge
    homebuilding_for_most_recent = homebuilding[homebuilding['date'] == most_recent_date].copy()
    homebuilding_for_building_recent = homebuilding[homebuilding['date'] == most_recent_homebuilding_date].copy()
    
    # Merge with homebuilding data on BOTH name and date
    zori_metro_most_recent = pd.merge(
        zori_metro_most_recent, 
        homebuilding_for_most_recent, 
        on=['name', 'date'],
        how='left', 
        suffixes=('_zori', '_homebuilding')
    )
    
    zori_metro_building_most_recent = pd.merge(
        zori_metro_building_most_recent, 
        homebuilding_for_building_recent, 
        on=['name', 'date'],
        how='left', 
        suffixes=('_zori', '_homebuilding')
    )
    
    # Save final datasets
    zori_metro_most_recent.to_csv(config.ZORI_METRO_MOST_RECENT, index=False)
    print(f"    ✓ Saved to: {config.ZORI_METRO_MOST_RECENT}")
    print(f"      Rows: {len(zori_metro_most_recent)}, Metros: {zori_metro_most_recent['name'].nunique()}")
    
    zori_metro_building_most_recent.to_csv(config.ZORI_METRO_BUILDING_MOST_RECENT, index=False)
    print(f"    ✓ Saved to: {config.ZORI_METRO_BUILDING_MOST_RECENT}")
    print(f"      Rows: {len(zori_metro_building_most_recent)}, Metros: {zori_metro_building_most_recent['name'].nunique()}")


def merge_and_finalize():
    """Main function to merge all data and create final outputs."""
    print("Starting data merge and finalization...\n")
    
    # Load top metros
    with open(config.TOP_METROS_PATH) as f:
        top_metros = json.load(f)
    
    # Load all raw data
    print("Loading raw data...")
    homebuilding_raw_all = pd.read_csv(config.HOMEBUILDING_RAW)
    homebuilding_raw_top = pd.read_csv(config.HOMEBUILDING_RAW_TOP)
    metros_pop = pd.read_csv(config.POPULATION_RAW)
    cities = pd.read_csv(config.CITIES_RAW)
    zori_county_wide = pd.read_csv(config.ZILLOW_COUNTY_RAW)
    zori_metro_wide = pd.read_csv(config.ZILLOW_METRO_RAW)
    print("  ✓ All raw data loaded")
    print(f"    - All metros: {homebuilding_raw_all['Name'].nunique()}")
    print(f"    - Top 50 metros: {homebuilding_raw_top['Name'].nunique()}\n")
    
    # Process each dataset - use top 50 for the main processing
    print("Processing datasets...")
    homebuilding = process_homebuilding_data(homebuilding_raw_top, metros_pop, top_metros)
    homebuilding_all = create_homebuilding_most_recent_all(homebuilding_raw_all, metros_pop, cities)  # NEW LINE
    zori_county_clean = process_zillow_county_data(zori_county_wide)
    zori_metro_long = process_zillow_metro_data(zori_metro_wide, cities, metros_pop, top_metros)
    print()
    
    # Create final merged datasets
    create_final_merged_datasets(zori_metro_long, homebuilding)
    
    print(f"\n✓ Data merge and finalization complete!")
    print(f"\nFinal outputs:")
    print(f"  - {config.HOMEBUILDING_CLEAN}")
    print(f"  - {config.HOMEBUILDING_MOST_RECENT_ALL}")  # NEW LINE
    print(f"  - {config.ZORI_COUNTY_CLEAN}")
    print(f"  - {config.ZORI_METRO_LONG}")
    print(f"  - {config.ZORI_METRO_MOST_RECENT}")
    print(f"  - {config.ZORI_METRO_BUILDING_MOST_RECENT}")


if __name__ == "__main__":
    merge_and_finalize()