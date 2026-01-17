"""Collect homebuilding permit data from US Census Bureau."""

import pandas as pd
import time
import random
import json
from datetime import date
import requests
from io import BytesIO
import xlrd

import sys
sys.path.append('.')

import config
from utils.date_helpers import generate_year_month_range
from utils.web_helpers import check_url_exists
from utils.cleaners import clean_metro_name


def process_2024_data(url, headers):
    """Process data from 2024 onwards."""
    # Download file with headers
    response = requests.get(url, headers=headers)
    response.raise_for_status()

    # Read Excel using xlrd directly to bypass pandas version check
    book = xlrd.open_workbook(file_contents=response.content)
    sheet = book.sheet_by_index(0)

    # Convert to dataframe, skipping first 7 rows
    data = []
    for row_idx in range(7, sheet.nrows):
        data.append([sheet.cell_value(row_idx, col_idx) for col_idx in range(sheet.ncols)])

    # Get headers from row 7 (index 7)
    headers_row = [sheet.cell_value(7, col_idx) for col_idx in range(sheet.ncols)]
    df = pd.DataFrame(data[1:], columns=headers_row)

    # Clean columns - drop empty column and metro/micro code
    df = df.loc[:, df.columns != '']  # Remove empty column names
    if 'Metro /Micro Code' in df.columns:
        df.drop(columns=['Metro /Micro Code'], inplace=True)
    
    # Clean column names and data
    df.columns = df.columns.str.replace('.1', '_ytd')
    df['Name'] = df['Name'].str.rstrip()
    
    # Add date - extract directly from URL
    date_part = url.split('_')[-1].replace('.xls', '')
    df['date'] = date_part
    
    return df


def process_2022_2023_data(url, headers):
    """Process data from 2022-2023."""
    # Download file with headers
    response = requests.get(url, headers=headers)
    response.raise_for_status()

    # Read Excel using xlrd directly to bypass pandas version check
    book = xlrd.open_workbook(file_contents=response.content)
    sheet = book.sheet_by_index(0)

    # Convert to dataframe, skipping first 7 rows
    data = []
    for row_idx in range(7, sheet.nrows):
        data.append([sheet.cell_value(row_idx, col_idx) for col_idx in range(sheet.ncols)])

    # Get headers from row 7 (index 7)
    headers_row = [sheet.cell_value(7, col_idx) for col_idx in range(sheet.ncols)]
    df = pd.DataFrame(data[1:], columns=headers_row)

    # Remove first row and clean columns
    df = df.loc[:, df.columns != '']  # Remove empty column names
    if 'Metro /Micro Code' in df.columns:
        df.drop(columns=['Metro /Micro Code'], inplace=True)
    
    # Clean column names and data
    df.columns = df.columns.str.replace('.1', '_ytd')
    df['Name'] = df['Name'].str.rstrip()
    
    # Add date - extract directly from URL
    date_part = url.split('_')[-1].replace('.xls', '')
    df['date'] = date_part
    
    return df


def process_pre_2022_data(url, headers):
    """Process data from 2021 and earlier."""
    # Download file with headers
    response = requests.get(url, headers=headers)
    response.raise_for_status()

    # Read Excel using xlrd directly to bypass pandas version check
    book = xlrd.open_workbook(file_contents=response.content)
    sheet = book.sheet_by_index(0)

    # Convert to dataframe, skipping first 7 rows
    data = []
    for row_idx in range(7, sheet.nrows):
        data.append([sheet.cell_value(row_idx, col_idx) for col_idx in range(sheet.ncols)])

    # Get headers from row 7 (index 7)
    headers_row = [sheet.cell_value(7, col_idx) for col_idx in range(sheet.ncols)]
    df = pd.DataFrame(data[1:], columns=headers_row)

    # Remove first row and clean columns
    df = df.loc[:, df.columns != '']  # Remove empty column names
    if 'Monthly Coverage Percent*' in df.columns:
        df.drop(columns=['Monthly Coverage Percent*'], inplace=True)
    if 'Metro /Micro Code' in df.columns:
        df.drop(columns=['Metro /Micro Code'], inplace=True)
    
    # Clean column names and data
    df.columns = df.columns.str.replace('.1', '_ytd')
    df['Name'] = df['Name'].str.rstrip()
    
    # Add date - extract directly from URL
    date_part = url.split('_')[-1].replace('.xls', '')
    df['date'] = date_part
    
    return df


def collect_homebuilding_data():
    """Collect all homebuilding data and save to raw data directory."""
    print("Starting homebuilding data collection...")
    
    # Load top metros
    with open(config.TOP_METROS_PATH) as f:
        top_metros = json.load(f)
    
    # Generate date range
    date_list = generate_year_month_range(years_back=config.YEARS_BACK)
    print(f"Collecting data for {len(date_list)} months...")
    
    # Initialize storage
    all_dfs = []
    headers = {'User-Agent': config.USER_AGENT}
    
    # Process each date
    for i, date_str in enumerate(date_list):
        year = int(date_str[:4])
        
        # Add delay between requests to avoid rate limiting
        if i > 0:
            time.sleep(random.uniform(config.REQUEST_DELAY_MIN, config.REQUEST_DELAY_MAX))
        
        try:
            # Determine URL format and processing function based on year
            if year >= 2024:
                url = config.CENSUS_BASE_URL_2024.format(date_str)
                process_func = process_2024_data
            else:
                url = config.CENSUS_BASE_URL_PRE2024.format(date_str)
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
        
        # Clean up the name column
        homebuilding['Name'] = homebuilding['Name'].apply(clean_metro_name)

        # Remove duplicate columns (keep first occurrence only)
        homebuilding = homebuilding.loc[:, ~homebuilding.columns.duplicated()]

        # Select and rename columns - KEEPING ALL UNIT TYPES
        homebuilding = homebuilding[['Name', 'Total', '1 Unit', '2 Units', '3 and 4 Units',
                                      '5 Units or More', 'date']]

        # Calculate multi-unit total
        homebuilding['multi_total'] = (homebuilding['2 Units'] +
                                        homebuilding['3 and 4 Units'] +
                                        homebuilding['5 Units or More'])
        
        # Save ALL metro areas version
        homebuilding.to_csv(config.HOMEBUILDING_RAW, index=False)
        print(f"\n✓ All metro areas saved to: {config.HOMEBUILDING_RAW}")
        print(f"  Total metro areas: {homebuilding['Name'].nunique()}")
        
        # Filter to top metros and save separate file
        homebuilding_top = homebuilding[homebuilding['Name'].isin(top_metros)]
        homebuilding_top.to_csv(config.HOMEBUILDING_RAW_TOP, index=False)
        print(f"✓ Top 50 metros saved to: {config.HOMEBUILDING_RAW_TOP}")
        print(f"  Top metro areas: {homebuilding_top['Name'].nunique()}")
        
        print(f"\n✓ Homebuilding data collection complete!")
        print(f"  Total rows collected: {len(homebuilding)}")
        print(f"  Date range: {homebuilding['date'].min()} to {homebuilding['date'].max()}")
        
        return homebuilding['date'].max()
    else:
        print("✗ No data was successfully processed")
        return None

if __name__ == "__main__":
    collect_homebuilding_data()