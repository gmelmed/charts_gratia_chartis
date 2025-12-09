import pandas as pd
import time
import sys
from pathlib import Path

# Add parent directory to path to import config
sys.path.insert(0, str(Path(__file__).parent.parent))
import config

import nfl_data_py as nfl

# Fetch all NFL games since the merger (1970-present)
# This includes both regular season and playoffs
print("Fetching all NFL games since the 1970 merger...")

# NOTE: nfl_data_py only provides schedule data from 1999-present
# For data from 1970-1998, you would need an alternative data source
# The nfl_data_py package focuses on the modern era with rich statistical data

# Get all available years (1999-present with full data)
years = list(range(1999, 2026))

all_games_list = []
for year in years:
    print(f"Fetching season {year}...")

    try:
        # Import schedule data for the year (includes regular season and playoffs)
        schedule = nfl.import_schedules([year])
        schedule['season'] = year
        all_games_list.append(schedule)
        print(f"Fetched season {year} with {schedule.shape[0]} games.")

        # Small delay to be respectful to the API
        time.sleep(0.5)
    except Exception as e:
        print(f"Error fetching season {year}: {e}")
        continue

# Combine all seasons
all_games = pd.concat(all_games_list, ignore_index=True)

# Save to csv
all_games.to_csv(config.NFL_ALL_GAMES, index=False)
print(f"All NFL games data saved to: {config.NFL_ALL_GAMES}")
print(f"Total games: {all_games.shape[0]}")
print(f"\nColumns available: {list(all_games.columns)}")
