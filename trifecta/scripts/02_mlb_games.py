import pandas as pd
import time
import sys
from pathlib import Path

# Add parent directory to path to import config
sys.path.insert(0, str(Path(__file__).parent.parent))
import config

# MLB-StatsAPI package (pip install MLB-StatsAPI)
import statsapi

# make a df of all mlb games using statsapi
# 2000 to present (2024 season)
all_games_list = []
for year in range(2000, 2026):
    print(f"Fetching season {year}...")

    # Retry logic with exponential backoff
    max_retries = 3
    retry_delay = 2  # Start with 2 seconds

    for attempt in range(max_retries):
        try:
            games = statsapi.schedule(start_date=f"{year}-03-01", end_date=f"{year}-11-30")
            games_df = pd.DataFrame(games)
            games_df['SEASON'] = year
            all_games_list.append(games_df)
            print(f"Fetched season {year} with {games_df.shape[0]} games.")

            # Success - break out of retry loop
            break

        except Exception as e:
            if attempt < max_retries - 1:
                wait_time = retry_delay * (2 ** attempt)  # Exponential backoff
                print(f"Error fetching season {year} (attempt {attempt + 1}/{max_retries}): {e}")
                print(f"Retrying in {wait_time} seconds...")
                time.sleep(wait_time)
            else:
                print(f"Failed to fetch season {year} after {max_retries} attempts: {e}")
                continue

    # Rate limiting: wait between successful requests to avoid timeout
    time.sleep(1.5)  # Increased from 0.5s to be more conservative

# Combine all seasons at the end
all_games = pd.concat(all_games_list, ignore_index=True)

# save to csv
all_games.to_csv(config.MLB_ALL_GAMES, index=False)
print(f"All MLB games data saved to: {config.MLB_ALL_GAMES}")