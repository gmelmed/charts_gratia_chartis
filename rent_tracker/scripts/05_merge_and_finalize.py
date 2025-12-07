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
    
    # Keep the original columns plus the running totals
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


def create_homebuilding_most_recent_all(homebuilding_raw_all, metros_pop, cities):
    """Create most recent homebuilding data for ALL metro areas with running totals."""
    print("  Creating most recent homebuilding dataset for all metros...")
    
    homebuilding_all = homebuilding_raw_all.copy()
    
    # Calculate multi-unit total
    homebuilding_all['multi_total'] = (homebuilding_all['2 Units'] + 
                                        homebuilding_all['3 and 4 Units'] + 
                                        homebuilding_all['5 Units or More'])
    
    # Lowercase columns
    homebuilding_all.columns = homebuilding_all.columns.str.lower()
    
    # Ensure the DataFrame is sorted by 'name' and 'date' for rolling calculations
    homebuilding_all = homebuilding_all.sort_values(by=['name', 'date'])
    
    # Create 12-month running totals BEFORE filtering to most recent
    homebuilding_all['rt'] = (
        homebuilding_all.groupby('name')['total']
        .rolling(window=12, min_periods=1)
        .sum()
        .reset_index(level=0, drop=True)
    )
    
    homebuilding_all['multi_rt'] = (
        homebuilding_all.groupby('name')['multi_total']
        .rolling(window=12, min_periods=1)
        .sum()
        .reset_index(level=0, drop=True)
    )
    
    # NOW filter to most recent date
    most_recent_date = homebuilding_all['date'].max()
    homebuilding_all = homebuilding_all[homebuilding_all['date'] == most_recent_date]
    
    # Merge with population data
    homebuilding_all = pd.merge(homebuilding_all, metros_pop, on='name', how='left')
    
    # Calculate per capita metrics (per 1000 people)
    homebuilding_all['rt_pc'] = (homebuilding_all['rt'] / homebuilding_all['population']) * 1000
    homebuilding_all['multi_rt_pc'] = (homebuilding_all['multi_rt'] / homebuilding_all['population']) * 1000
    
    # Merge with cities for lat/lng
    homebuilding_all = pd.merge(homebuilding_all, cities[['name', 'lat', 'lng']], 
                                  on='name', how='left')
    
    # Add region
    homebuilding_all['region'] = homebuilding_all['name'].map(config.REGION_MAP)
    
    # Select final columns
    homebuilding_all = homebuilding_all[['name', 'date', 'total', '1 unit', '2 units', 
                                          '3 and 4 units', '5 units or more', 'multi_total',
                                          'rt', 'multi_rt', 'population', 'rt_pc', 'multi_rt_pc',
                                          'lat', 'lng', 'region']]
    
    # Save
    homebuilding_all.to_csv(config.HOMEBUILDING_MOST_RECENT_ALL, index=False)
    print(f"    ✓ Saved to: {config.HOMEBUILDING_MOST_RECENT_ALL}")
    print(f"      Rows: {len(homebuilding_all)}, Metros: {homebuilding_all['name'].nunique()}")
    print(f"      Date: {most_recent_date}")
    
    return homebuilding_all


def process_zillow_county_data(zori_county_wide):
    """Process Zillow county data to calculate changes."""
    print("  Processing Zillow county data...")

    # Get date columns
    date_cols = [col for col in zori_county_wide.columns if col not in ['fips', 'region_name']]
    date_cols_dt = pd.to_datetime(date_cols)

    most_recent_date = date_cols_dt.max()
    most_recent_col = most_recent_date.strftime('%Y-%m-%d')

    # Calculate one-year change
    one_year_date = most_recent_date - pd.DateOffset(years=1)

    # Find the closest matching column for this date
    one_year_col = min(date_cols, key=lambda x: abs(pd.to_datetime(x) - one_year_date))

    # Create the new dataframe
    zori_county_clean = pd.DataFrame({
        'region_name': zori_county_wide['region_name'],
        'fips': zori_county_wide['fips'],
        'most_recent_date': most_recent_date,
        'most_recent_value': zori_county_wide[most_recent_col],
        'one_year_date': pd.to_datetime(one_year_col),
        'one_year_value': zori_county_wide[one_year_col],
        'one_year_change': ((zori_county_wide[most_recent_col] - zori_county_wide[one_year_col]) /
                            zori_county_wide[one_year_col] * 100)
    })

    # Ensure proper data types
    zori_county_clean['fips'] = zori_county_clean['fips'].astype(int)
    zori_county_clean['region_name'] = zori_county_clean['region_name'].astype(str)

    # Save to csv
    zori_county_clean.to_csv(config.ZORI_COUNTY_CLEAN, index=False)
    print(f"    ✓ Saved to: {config.ZORI_COUNTY_CLEAN}")

    return zori_county_clean


def process_zillow_metro_generic(zillow_wide, cities, metros_pop, top_metros,
                                  value_col_name, change_type, output_path, dataset_name):
    """Generic function to process Zillow metro data into long format with changes.

    Args:
        zillow_wide: Wide format Zillow dataframe
        cities: Cities dataframe with lat/lng
        metros_pop: Population dataframe
        top_metros: List of top metro names to filter
        value_col_name: Name for the value column (e.g., 'zori', 'affordability_index')
        change_type: 'pct' for percentage change, 'diff' for absolute difference
        output_path: Path to save the processed data
        dataset_name: Name for logging (e.g., 'Zillow metro', 'Zillow metro affordability')
    """
    print(f"  Processing {dataset_name} data...")

    index_cols = ['RegionID', 'SizeRank', 'RegionName', 'RegionType', 'StateName']

    # Melt df
    data_long = pd.melt(
        zillow_wide,
        id_vars=index_cols,
        value_vars=[col for col in zillow_wide.columns if col not in index_cols],
        var_name="date",
        value_name=value_col_name
    )

    data_long['date'] = pd.to_datetime(data_long['date'])

    # Increase date by one day
    data_long['date'] += pd.Timedelta(days=1)

    data_long = data_long[['RegionName', 'date', value_col_name]]
    data_long.rename(columns={'RegionName': 'name'}, inplace=True)

    # Merge with cities to get lat/lon (excluding population as it will come from metros_pop)
    data_long = pd.merge(data_long, cities[['name', 'lat', 'lng']], on='name', how='left')

    # Calculate 1-year change
    data_long = data_long.sort_values(by=['name', 'date'])
    if change_type == 'pct':
        data_long['one_year_change'] = (data_long.groupby('name')[value_col_name]
                                        .pct_change(periods=12, fill_method=None) * 100)
    elif change_type == 'diff':
        data_long['one_year_change'] = (data_long.groupby('name')[value_col_name]
                                        .diff(periods=12))

    # Save the date of one year comparison
    data_long['one_year_date'] = data_long['date'] - pd.DateOffset(years=1)

    # Filter to top metros
    data_long = data_long[data_long['name'].isin(top_metros)]

    # Save long format data
    data_long.to_csv(output_path, index=False)
    print(f"    ✓ Saved to: {output_path}")

    # Merge with metros_pop
    data_long = pd.merge(data_long, metros_pop, on='name', how='left')

    return data_long


def process_zillow_metro_data(zori_metro_wide, cities, metros_pop, top_metros):
    """Process Zillow metro data into long format with changes."""
    return process_zillow_metro_generic(
        zori_metro_wide, cities, metros_pop, top_metros,
        value_col_name='zori',
        change_type='pct',
        output_path=config.ZORI_METRO_LONG,
        dataset_name='Zillow metro'
    )


def process_zillow_affordability_data(zori_affordability_wide, cities, metros_pop, top_metros):
    """Process Zillow metro affordability data into long format with changes."""
    return process_zillow_metro_generic(
        zori_affordability_wide, cities, metros_pop, top_metros,
        value_col_name='affordability_index',
        change_type='diff',
        output_path=config.ZORI_AFFORDABILITY_LONG,
        dataset_name='Zillow metro affordability'
    )

def create_final_merged_datasets(zori_metro_long, homebuilding):
    """Create final merged datasets with most recent data."""
    print("  Creating final merged datasets...")

    # Get most recent dates
    most_recent_zori_date = zori_metro_long['date'].max()
    most_recent_homebuilding_date = homebuilding['date'].max()

    # Create most recent ZORI dataset (without homebuilding)
    zori_metro_most_recent = zori_metro_long[zori_metro_long['date'] == most_recent_zori_date].copy()

    # Save ZORI-only most recent dataset
    zori_metro_most_recent.to_csv(config.ZORI_METRO_MOST_RECENT, index=False)
    print(f"    ✓ Saved to: {config.ZORI_METRO_MOST_RECENT}")
    print(f"      Rows: {len(zori_metro_most_recent)}, Metros: {zori_metro_most_recent['name'].nunique()}")

    # Create ZORI + Homebuilding merged dataset with most recent homebuilding data
    # Filter ZORI to just metros that have homebuilding data at the most recent homebuilding date
    zori_at_homebuilding_date = zori_metro_long[zori_metro_long['date'] == most_recent_homebuilding_date].copy()
    homebuilding_most_recent = homebuilding[homebuilding['date'] == most_recent_homebuilding_date].copy()

    # Merge on name only (since we've already filtered both to the same date)
    zori_metro_homebuilding_most_recent = pd.merge(
        zori_at_homebuilding_date,
        homebuilding_most_recent,
        on='name',
        how='inner',  # Only keep metros that have both ZORI and homebuilding data
        suffixes=('_zori', '_homebuilding')
    )

    # Save merged dataset
    zori_metro_homebuilding_most_recent.to_csv(config.ZORI_METRO_BUILDING_MOST_RECENT, index=False)
    print(f"    ✓ Saved to: {config.ZORI_METRO_BUILDING_MOST_RECENT}")
    print(f"      Rows: {len(zori_metro_homebuilding_most_recent)}, Metros: {zori_metro_homebuilding_most_recent['name'].nunique()}")

    return zori_metro_homebuilding_most_recent


def create_wide_homebuilding_timeseries(zori_metro_homebuilding_most_recent, homebuilding):
    """Create a wide format dataset with rt_pc values for each month as columns (last 12 months only)."""
    print("  Creating wide format homebuilding timeseries...")

    # Get most recent date and filter to last 12 months
    most_recent_date = homebuilding['date'].max()
    one_year_ago = most_recent_date - pd.DateOffset(months=24)

    # Filter homebuilding data to last 12 months
    homebuilding_last_year = homebuilding[homebuilding['date'] > one_year_ago].copy()

    # Pivot the homebuilding data to get rt_pc for each date
    homebuilding_pivot = homebuilding_last_year.pivot(
        index='name',
        columns='date',
        values='rt_pc'
    )

    # Convert column names (dates) to string format YYYY-MM-DD
    homebuilding_pivot.columns = homebuilding_pivot.columns.strftime('%Y-%m-%d')

    # Reset index to make 'name' a column again
    homebuilding_pivot = homebuilding_pivot.reset_index()

    # Merge with the zori_metro_homebuilding_most_recent data
    zori_homebuilding_wide = pd.merge(
        zori_metro_homebuilding_most_recent,
        homebuilding_pivot,
        on='name',
        how='left'
    )

    # Save the wide format dataset
    output_path = config.PROCESSED_DATA_DIR + 'zori_metro_homebuilding_timeseries_wide.csv'
    zori_homebuilding_wide.to_csv(output_path, index=False)
    print(f"    ✓ Saved to: {output_path}")
    print(f"      Rows: {len(zori_homebuilding_wide)}, Metros: {zori_homebuilding_wide['name'].nunique()}")
    print(f"      Date columns: {len([c for c in zori_homebuilding_wide.columns if c[0].isdigit()])}")
    print(f"      Date range: {one_year_ago.strftime('%Y-%m-%d')} to {most_recent_date.strftime('%Y-%m-%d')}")

    return zori_homebuilding_wide


def create_affordability_most_recent(zori_affordability_long):
    """Create most recent affordability dataset."""
    print("  Creating most recent affordability dataset...")

    # Get most recent date
    most_recent_date = zori_affordability_long['date'].max()

    # Filter to most recent date
    zori_affordability_most_recent = zori_affordability_long[zori_affordability_long['date'] == most_recent_date].copy()

    # Save most recent affordability dataset
    zori_affordability_most_recent.to_csv(config.ZORI_AFFORDABILITY_MOST_RECENT, index=False)
    print(f"    ✓ Saved to: {config.ZORI_AFFORDABILITY_MOST_RECENT}")
    print(f"      Rows: {len(zori_affordability_most_recent)}, Metros: {zori_affordability_most_recent['name'].nunique()}")
    print(f"      Date: {most_recent_date}")

    return zori_affordability_most_recent


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
    zori_affordability_wide = pd.read_csv(config.ZILLOW_AFFORDABILITY_RAW)
    print("  ✓ All raw data loaded")
    print(f"    - All metros: {homebuilding_raw_all['Name'].nunique()}")
    print(f"    - Top 50 metros: {homebuilding_raw_top['Name'].nunique()}\n")
    
    # Process each dataset
    print("Processing datasets...")
    homebuilding = process_homebuilding_data(homebuilding_raw_top, metros_pop, top_metros)
    homebuilding_all = create_homebuilding_most_recent_all(homebuilding_raw_all, metros_pop, cities)
    zori_county_clean = process_zillow_county_data(zori_county_wide)
    zori_metro_long = process_zillow_metro_data(zori_metro_wide, cities, metros_pop, top_metros)
    zori_affordability_long = process_zillow_affordability_data(zori_affordability_wide, cities, metros_pop, top_metros)
    print()

    # Create final merged datasets
    zori_metro_homebuilding_most_recent = create_final_merged_datasets(zori_metro_long, homebuilding)

    # Create wide format timeseries dataset
    create_wide_homebuilding_timeseries(zori_metro_homebuilding_most_recent, homebuilding)

    # Create affordability most recent dataset
    create_affordability_most_recent(zori_affordability_long)

    print(f"\n✓ Data merge and finalization complete!")
    print(f"\nFinal outputs:")
    print(f"  - {config.HOMEBUILDING_CLEAN}")
    print(f"  - {config.HOMEBUILDING_MOST_RECENT_ALL}")
    print(f"  - {config.ZORI_COUNTY_CLEAN}")
    print(f"  - {config.ZORI_METRO_LONG}")
    print(f"  - {config.ZORI_METRO_MOST_RECENT}")
    print(f"  - {config.ZORI_METRO_BUILDING_MOST_RECENT}")
    print(f"  - {config.ZORI_AFFORDABILITY_LONG}")
    print(f"  - {config.ZORI_AFFORDABILITY_MOST_RECENT}")
    print(f"  - {config.PROCESSED_DATA_DIR}zori_metro_homebuilding_timeseries_wide.csv")


if __name__ == "__main__":
    merge_and_finalize()
