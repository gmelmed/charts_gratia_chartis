import pandas as pd


# save county centroids data
county_centroids_url = "https://www2.census.gov/geo/docs/reference/cenpop2020/county/CenPop2020_Mean_CO.txt"
county_centroids = pd.read_csv(county_centroids_url)

# create fips column
county_centroids['fips'] = county_centroids['STATEFP'] * 1000 + county_centroids['COUNTYFP']

# lowercase column names
county_centroids.columns = county_centroids.columns.str.lower()

# save to csv
county_centroids.to_csv('rent_tracker/data/county_centroids.csv', index=False)