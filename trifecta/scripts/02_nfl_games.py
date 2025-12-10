import pandas as pd
import time
import sys
from pathlib import Path
import os
import json

# Add parent directory to path to import config
sys.path.insert(0, str(Path(__file__).parent.parent))
import config

import nfl_data_py as nfl

market_teams_path = Path(__file__).parent.parent / 'data' / 'markets_teams.json'
with open(market_teams_path, 'r') as f:
    markets_data = json.load(f)
    
nfl_teams = []
for market in markets_data['markets_teams']:
    for team in market['teams']:
        if team['league'] == 'NFL':
            nfl_teams.append({
                'name': team['name'],
                'api_id': team['api_id']
            })

raw_data_dir = Path(__file__).parent.parent / 'data' / 'raw'
raw_data_dir.mkdir(parents=True, exist_ok=True)

print(f"Found {len(nfl_teams)} NFL teams to fetch data for")

def fetch_nfl_data(season, team_api_id):
    """Fetch NFL data for a given season and team."""
    try:
        games = nfl.import_team_games([season], team=team_api_id)
        return games
    except Exception as e:
        print(f"Error fetching data for team {team_api_id} in season {season}: {e}")
        return pd.DataFrame()

# Get all years from 2000 to present
years = list(range(2000, 2026))

for team in nfl_teams:
    print(f"\n=== Fetching data for team: {team['name']} (ID: {team['api_id']}) ===")
    team_all_seasons = []
    for year in years:
        print(f"  Fetching season {year}...")
        season_data = fetch_nfl_data(year, team['api_id'])
        if not season_data.empty:
            team_all_seasons.append(season_data)
        time.sleep(0.5)

    if team_all_seasons:
        team_df = pd.concat(team_all_seasons, ignore_index=True)
        team_file_path = raw_data_dir / f"nfl_{team['name'].lower().replace(' ', '_')}_games.csv"
        team_df.to_csv(team_file_path, index=False)
        print(f"  Saved data for {team['name']} to {team_file_path}")
    else:
        print(f"  No data found for {team['name']}")

print("\n===ALL NFL TEAMS DATA FETCHED AND SAVED===")
print(f"Raw data directory: {raw_data_dir}")