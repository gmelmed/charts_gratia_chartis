from nba_api.stats.endpoints import leaguegamefinder
import pandas as pd
import time
import sys
from pathlib import Path

# Add parent directory to path to import config
sys.path.insert(0, str(Path(__file__).parent.parent))
import config

# make a df of all nba games using nba_api

# 1970 to present (2025-2026 season)
all_games_list = []
for i in range(1970, 2026):
    season_str = f"{i}-{str(i+1)[-2:]}"
    print(f"Fetching season {season_str}...")

    try:
        # Specify the season in the API call
        gamefinder = leaguegamefinder.LeagueGameFinder(season_nullable=season_str, league_id_nullable='00')
        games = gamefinder.get_data_frames()[0]
        games['SEASON'] = season_str
        all_games_list.append(games)
        print(f"Fetched season {season_str} with {games.shape[0]} games.")

        # Rate limiting: wait between requests to avoid timeout
        time.sleep(0.6)  # NBA API recommends ~600ms between requests
    except Exception as e:
        print(f"Error fetching season {season_str}: {e}")
        continue

# Combine all seasons at the end
all_games = pd.concat(all_games_list, ignore_index=True)

# save to csv
all_games.to_csv(config.NBA_ALL_GAMES, index=False)
print(f"All NBA games data saved to: {config.NBA_ALL_GAMES}")
