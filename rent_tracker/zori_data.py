import pandas as pd
import time
import random
import requests
from datetime import datetime, date
from dateutil.relativedelta import relativedelta
from typing import List
import re

# read in rent_tracker/data/top_metros.json as a list
import json
with open('rent_tracker/data/top_metros.json') as f:
    top_metros = json.load(f)
    
region_map = {
    "New York, NY":"Northeast","Los Angeles, CA":"West","Chicago, IL":"Midwest",
    "Dallas, TX":"Southwest","Houston, TX":"Southwest","Atlanta, GA":"Southeast",
    "Washington, DC":"Northeast","Philadelphia, PA":"Northeast","Miami, FL":"Southeast",
    "Phoenix, AZ":"Southwest","Boston, MA":"Northeast","Riverside, CA":"West",
    "San Francisco, CA":"West","Detroit, MI":"Midwest","Seattle, WA":"West",
    "Minneapolis, MN":"Midwest","Tampa, FL":"Southeast","San Diego, CA":"West",
    "Denver, CO":"West","Baltimore, MD":"Northeast","Orlando, FL":"Southeast",
    "Charlotte, NC":"Southeast","St. Louis, MO":"Midwest","San Antonio, TX":"Southwest",
    "Portland, OR":"West","Austin, TX":"Southwest","Pittsburgh, PA":"Northeast",
    "Sacramento, CA":"West","Las Vegas, NV":"West","Cincinnati, OH":"Midwest",
    "Kansas City, MO":"Midwest","Columbus, OH":"Midwest","Indianapolis, IN":"Midwest",
    "Nashville, TN":"Southeast","Cleveland, OH":"Midwest","San Jose, CA":"West",
    "Virginia Beach, VA":"Southeast","Jacksonville, FL":"Southeast","Providence, RI":"Northeast",
    "Milwaukee, WI":"Midwest","Raleigh, NC":"Southeast","Oklahoma City, OK":"Southwest",
    "Louisville, KY":"Southeast","Richmond, VA":"Southeast","Memphis, TN":"Southeast",
    "Salt Lake City, UT":"West","Birmingham, AL":"Southeast","Grand Rapids, MI":"Midwest",
    "Buffalo, NY":"Northeast","Hartford, CT":"Northeast"
}


# homebuilding data

def generate_year_month_range(end_date: date = None, years_back: int = 6) -> List[str]:
    """
    Generate a list of year-month combinations in 'yyyymm' format,
    starting from the specified end date and going back a specified number of years.

    Args:
        end_date (date, optional): The end date to start from. Defaults to today's date.
        years_back (int, optional): Number of years to go back. Defaults to 6.

    Returns:
        List[str]: List of year-month combinations in 'yyyymm' format, sorted in descending order.

    Example:
        >>> generate_year_month_range()  # If today is 2024-11-14
        ['202411', '202410', '202409', ..., '201812']
    """
    # If no end date is provided, use today's date
    if end_date is None:
        end_date = date.today()

    # Calculate start date
    start_date = end_date - relativedelta(years=years_back)

    # Initialize result list
    date_list = []

    # Current date for iteration
    current_date = end_date

    # Generate dates until we reach start date
    while current_date >= start_date:
        # Format date as 'yyyymm'
        date_str = current_date.strftime('%Y%m')
        date_list.append(date_str)
        # Move to previous month
        current_date -= relativedelta(months=1)

    return date_list

# Example usage
if __name__ == "__main__":
    date_list = generate_year_month_range()
    print(f"Generated {len(date_list)} year-month combinations:")
    print(date_list[:12])  # Print first year as example

def check_url_exists(url):
    """Check if a URL exists without downloading the full file"""
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleBoxKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    try:
        response = requests.head(url, headers=headers, timeout=10)
        return response.status_code == 200
    except:
        return False

def process_2024_data(url, headers):
    """Process data from 2024 onwards"""
    df = pd.read_excel(url, skiprows=7, storage_options=headers)
    
    # Clean columns
    df.drop(columns=['Metro /Micro Code', 'Unnamed: 10'], inplace=True)
    
    # Clean column names and data
    df.columns = df.columns.str.replace('.1', '_ytd')
    df['Name'] = df['Name'].str.rstrip()
    
    # Add date - extract directly from URL
    date_part = url.split('_')[-1].replace('.xls', '')
    df['date'] = date_part
    
    return df

def process_2022_2023_data(url, headers):
    """Process data from 2022-2023"""
    df = pd.read_excel(url, skiprows=7, storage_options=headers)
    
    # Remove first row and clean columns
    df = df.iloc[1:]
    df.drop(columns=['Unnamed: 9'], inplace=True)
    
    # Clean column names and data
    df.columns = df.columns.str.replace('.1', '_ytd')
    df['Name'] = df['Name'].str.rstrip()
    
    # Add date - extract directly from URL
    date_part = url.split('_')[-1].replace('.xls', '')
    df['date'] = date_part
    
    return df

def process_pre_2022_data(url, headers):
    """Process data from 2021 and earlier"""
    df = pd.read_excel(url, skiprows=7, storage_options=headers)
    
    # Remove first row and clean columns
    df = df.iloc[1:]
    df.drop(columns=['Monthly Coverage Percent*', 'Unnamed: 10'], inplace=True)
    
    # Clean column names and data
    df.columns = df.columns.str.replace('.1', '_ytd')
    df['Name'] = df['Name'].str.rstrip()
    
    # Add date - extract directly from URL
    date_part = url.split('_')[-1].replace('.xls', '')
    df['date'] = date_part
    
    return df

# Initialize an empty list to store all dataframes
all_dfs = []

# Set up headers
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
}

# Process each date
for i, date_str in enumerate(date_list):
    year = int(date_str[:4])
    
    # Add delay between requests (2-4 seconds) to avoid rate limiting
    if i > 0:
        time.sleep(random.uniform(2, 4))
    
    try:
        # Determine URL format and processing function based on year
        if year >= 2024:
            url = f'https://www.census.gov/construction/bps/xls/cbsamonthly_{date_str}.xls'
            process_func = process_2024_data
        else:
            url = f'https://www.census.gov/construction/bps/xls/msamonthly_{date_str}.xls'
            if year >= 2022:
                process_func = process_2022_2023_data
            else:
                process_func = process_pre_2022_data
        
        # Check if URL exists
        if check_url_exists(url):
            try:
                df = process_func(url, headers)
                all_dfs.append(df)
                print(f"✓ Successfully processed data for {date_str}")
            except Exception as e:
                print(f"✗ Error processing {date_str}: {str(e)}")
                continue
        else:
            print(f"○ No data available for {date_str}")
            continue
            
    except Exception as e:
        print(f"✗ Error with {date_str}: {str(e)}")
        continue

# Concatenate all dataframes if we have any data
if all_dfs:
    homebuilding = pd.concat(all_dfs, ignore_index=True)
    
    # Convert date column to datetime
    homebuilding['date'] = pd.to_datetime(homebuilding['date'], format='%Y%m')
    
    # Sort by date and other relevant columns
    homebuilding = homebuilding.sort_values(['date', 'Name'], ascending=[False, True])
    
    print(f"\nFinal dataset contains {len(homebuilding)} rows from {len(all_dfs)} different months")
    print(f"Date range: {homebuilding['date'].min()} to {homebuilding['date'].max()}")
else:
    print("No data was successfully processed")
    homebuilding = pd.DataFrame()
    
    
# clean up the name column
homebuilding['Name'] = homebuilding['Name'].apply(lambda x: x.split(',')[0].split('-')[0] + ',' + x.split(',')[1].split('-')[0])

homebuilding = homebuilding[['Name', 'Total', '1 Unit', '2 Units', '3 and 4 Units',
       '5 Units or More', 'date']]
homebuilding['multi_total'] = homebuilding['2 Units'] + homebuilding['3 and 4 Units'] + homebuilding['5 Units or More']

# lowercase columns
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

homebuilding = homebuilding[['name', 'date', 'rt', 'multi_rt']]

# save most recent homebuilding data
most_recent_homebuilding_date = homebuilding['date'].max()

# include only data for top metros
homebuilding = homebuilding[homebuilding['name'].isin(top_metros)]

homebuilding['region'] = homebuilding['name'].map(region_map)



# metro population data

# read in metro population data
population_link = "https://www2.census.gov/programs-surveys/popest/tables/2020-2024/metro/totals/cbsa-met-est2024-pop.xlsx"

# read in us cities data
cities = pd.read_csv('rent_tracker/data/uscities.csv')

# form name column
cities['name'] = cities['city_ascii'] + ", " + cities['state_id']

# only necessary cols
cities = cities[['name', 'lat', 'lng', 'population']]

# read in excel, skipping first 3 rows
metros_pop = pd.read_excel(population_link, skiprows=3)
metros_pop['Unnamed: 0'] = metros_pop['Unnamed: 0'].str.lstrip('.')

# rename column
metros_pop = metros_pop.rename(columns={'Unnamed: 0': 'name'})

# remove rows where name doesn't contain "Metro Area"
metros_pop = metros_pop[metros_pop['name'].str.contains('Metro Area', na=False)]

# delete " Metro Area" from name column
metros_pop['name'] = metros_pop['name'].str.replace(' Metro Area', '', regex=False)

# clean up the name column
metros_pop['name'] = metros_pop['name'].apply(lambda x: x.split(',')[0].split('-')[0] + ',' + x.split(',')[1].split('-')[0])

metros_pop.drop(columns=['Unnamed: 1'], inplace=True)

# turn all col names to strings
metros_pop.columns = metros_pop.columns.map(str)

# keep only name and 2024 columns, rename 2024 to population
metros_pop = metros_pop[['name', '2024']].rename(columns={'2024': 'population'})

# merge homebuilding with metros_pop
homebuilding = pd.merge(homebuilding, metros_pop, on='name', how='inner')

homebuilding['rt_pc'] = homebuilding['rt'] / homebuilding['population']
homebuilding['multi_rt_pc'] = homebuilding['multi_rt'] / homebuilding['population']

# change per capita columns to per 1000
for col in homebuilding.columns:
    if 'pc' in col:
        homebuilding[col] = homebuilding[col] * 1000
        
        
homebuilding.to_csv('rent_tracker/data/homebuilding_clean.csv', index=False)



# ZILLOW OPEN RENT DATA

# county data

# read in the zori county wide data
county_wide_url = "https://files.zillowstatic.com/research/public_csvs/zori/County_zori_uc_sfrcondomfr_sm_month.csv?t=1734717130"
zori_county_wide = pd.read_csv(county_wide_url)

# clean
zori_county_wide.drop(columns=['RegionID', 'SizeRank', 'RegionType', 'StateName', 'Metro'], inplace=True)

# calculate fips
zori_county_wide['fips'] = zori_county_wide['StateCodeFIPS'] * 1000 + zori_county_wide['MunicipalCodeFIPS']

# drop state and municipal code fips
zori_county_wide.drop(columns=['StateCodeFIPS', 'MunicipalCodeFIPS'], inplace=True)

# create region name
zori_county_wide['region_name'] = zori_county_wide['RegionName'] + ", " + zori_county_wide['State']

# drop region name and state columns
zori_county_wide.drop(columns=['RegionName', 'State'], inplace=True)

# Fix: Create the boolean mask or list separately
date_cols = [col for col in zori_county_wide.columns if col not in ['fips', 'region_name']]

date_cols_dt = pd.to_datetime(date_cols)

most_recent_date = date_cols_dt.max()
most_recent_col = most_recent_date.strftime('%Y-%m-%d')

# calculate one-year and five-year changes
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
    'one_year_change': ((zori_county_wide[most_recent_col] - zori_county_wide[one_year_col]) / zori_county_wide[one_year_col] * 100),
    'five_year_date': pd.to_datetime(five_year_col),
    'five_year_value': zori_county_wide[five_year_col],
    'five_year_change': ((zori_county_wide[most_recent_col] - zori_county_wide[five_year_col]) / zori_county_wide[five_year_col] * 100)
})

# Ensure proper data types
zori_county_clean['fips'] = zori_county_clean['fips'].astype(int)
zori_county_clean['region_name'] = zori_county_clean['region_name'].astype(str)

# save to csv
zori_county_clean.to_csv('rent_tracker/data/zori_county_clean.csv', index=False)






# zillow data for metro areas
metro_url = "https://files.zillowstatic.com/research/public_csvs/zori/Metro_zori_uc_sfrcondomfr_sm_month.csv?t=1734717130"

zori_metro_wide = pd.read_csv(metro_url)

index_cols = ['RegionID', 'SizeRank', 'RegionName', 'RegionType', 'StateName'] 

# melt df
zori_metro_long = pd.melt(
    zori_metro_wide,
    id_vars = index_cols,
    value_vars = [col for col in zori_metro_wide.columns if col not in index_cols],
    var_name = "date",
    value_name = "zori"
)

zori_metro_long['date'] = pd.to_datetime(zori_metro_long['date'])

# increase date by one day
zori_metro_long['date'] += pd.Timedelta(days=1)

zori_metro_long = zori_metro_long[['RegionName', 'date', 'zori']]

zori_metro_long.rename(columns={'RegionName': 'name'}, inplace=True)

# merge with cities to get lat/lon/population
zori_metro_long = pd.merge(zori_metro_long, cities, on='name', how='left')

# calculate 1-year and 5-year changes
zori_metro_long = zori_metro_long.sort_values(by=['name', 'date'])
zori_metro_long['one_year_change'] = zori_metro_long.groupby('name')['zori'].pct_change(periods=12) * 100
zori_metro_long['five_year_change'] = zori_metro_long.groupby('name')['zori'].pct_change(periods=60) * 100

# save the date of one year and five year comparisons
zori_metro_long['one_year_date'] = zori_metro_long['date'] - pd.DateOffset(years=1)
zori_metro_long['five_year_date'] = zori_metro_long['date'] - pd.DateOffset(years=5)


zori_metro_long = zori_metro_long[zori_metro_long['name'].isin(top_metros)]

zori_metro_long.to_csv('rent_tracker/data/zori_metro_long.csv', index=False)

# merge with metros_pop
zori_metro_long = pd.merge(zori_metro_long, metros_pop, on='name', how='left')

# make a df with most recent data only
most_recent_date = zori_metro_long['date'].max()
zori_metro_most_recent = zori_metro_long[zori_metro_long['date'] == most_recent_date]
zori_metro_building_most_recent = zori_metro_long[zori_metro_long['date'] == most_recent_homebuilding_date]

# merge with homebuilding data
zori_metro_most_recent = pd.merge(zori_metro_most_recent, homebuilding, on='name', how='left', suffixes=('_zori', '_homebuilding'))
zori_metro_building_most_recent = pd.merge(zori_metro_building_most_recent, homebuilding, on='name', how='left', suffixes=('_zori', '_homebuilding'))


zori_metro_most_recent.to_csv('rent_tracker/data/zori_metro_most_recent.csv', index=False)
zori_metro_building_most_recent.to_csv('rent_tracker/data/zori_metro_homebuilding_most_recent.csv', index=False)



