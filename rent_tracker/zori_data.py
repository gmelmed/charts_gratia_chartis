import pandas as pd

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