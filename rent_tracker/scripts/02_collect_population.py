"""Collect metro population data from US Census Bureau."""

import pandas as pd
import json

import sys
sys.path.append('.')

import config
from utils.cleaners import clean_metro_name


def collect_population_data():
    """Collect metro population data and city geographic data."""
    print("Starting population data collection...")
    
    # Load top metros
    with open(config.TOP_METROS_PATH) as f:
        top_metros = json.load(f)
    
    # Read in metro population data
    print("  Fetching metro population data...")
    metros_pop = pd.read_excel(config.POPULATION_URL, skiprows=3)
    metros_pop['Unnamed: 0'] = metros_pop['Unnamed: 0'].str.lstrip('.')
    
    # Rename column
    metros_pop = metros_pop.rename(columns={'Unnamed: 0': 'name'})
    
    # Remove rows where name doesn't contain "Metro Area"
    metros_pop = metros_pop[metros_pop['name'].str.contains('Metro Area', na=False)]
    
    # Delete " Metro Area" from name column
    metros_pop['name'] = metros_pop['name'].str.replace(' Metro Area', '', regex=False)
    
    # Clean up the name column
    metros_pop['name'] = metros_pop['name'].apply(clean_metro_name)
    
    metros_pop.drop(columns=['Unnamed: 1'], inplace=True)
    
    # Turn all col names to strings
    metros_pop.columns = metros_pop.columns.map(str)
    
    # Keep only name and 2024 columns, rename 2024 to population
    metros_pop = metros_pop[['name', '2024']].rename(columns={'2024': 'population'})
    
    # Save metro population data
    metros_pop.to_csv(config.POPULATION_RAW, index=False)
    print(f"  ✓ Metro population data saved to: {config.POPULATION_RAW}")
    
    # Read in US cities data
    print("  Loading US cities geographic data...")
    cities = pd.read_csv(config.USCITIES_PATH)
    
    # Form name column
    cities['name'] = cities['city_ascii'] + ", " + cities['state_id']
    
    # Only necessary cols
    cities = cities[['name', 'lat', 'lng', 'population']]
    
    # Save cities data
    cities.to_csv(config.CITIES_RAW, index=False)
    print(f"  ✓ Cities geographic data saved to: {config.CITIES_RAW}")
    
    print(f"\n✓ Population data collection complete!")
    print(f"  Metro areas: {len(metros_pop)}")
    print(f"  Cities: {len(cities)}")


if __name__ == "__main__":
    collect_population_data()