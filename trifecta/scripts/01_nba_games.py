from nba_api.stats.endpoints import leaguegamefinder
import pandas as pd
import time
import sys
import json
from pathlib import Path
import os

# Add parent directory to path to import config
sys.path.insert(0, str(Path(__file__).parent.parent))
import config

# Load NBA teams from markets_teams.json
markets_teams_path = Path(__file__).parent.parent / 'data' / 'markets_teams.json'
with open(markets_teams_path, 'r') as f:
    markets_data = json.load(f)

# Extract all NBA teams
nba_teams = []
for market in markets_data['markets_teams']:
    for team in market['teams']:
        if team['league'] == 'NBA':
            nba_teams.append({
                'name': team['name'],
                'api_id': team['api_id']
            })

print(f"Found {len(nba_teams)} NBA teams to fetch data for")

# Create raw data directory if it doesn't exist
raw_data_dir = Path(__file__).parent.parent / 'data' / 'raw'
raw_data_dir.mkdir(parents=True, exist_ok=True)

# Season types to fetch
season_types = ['Regular Season', 'Playoffs', 'PlayIn']

def fetch_with_retry(season_str, season_type, team_api_id, max_retries=3):
    """Fetch data with exponential backoff retry logic"""
    for attempt in range(max_retries):
        try:
            gamefinder = leaguegamefinder.LeagueGameFinder(
                season_nullable=season_str,
                league_id_nullable='00',
                season_type_nullable=season_type,
                team_id_nullable=str(team_api_id),
                # outcome_nullable='W',
                timeout=60  # Increase timeout to 60 seconds
            )
            games = gamefinder.get_data_frames()[0]
            return games
        except Exception as e:
            if attempt < max_retries - 1:
                wait_time = (2 ** attempt) * 2  # Exponential backoff: 2s, 4s, 8s
                print(f"  Attempt {attempt + 1} failed: {e}")
                print(f"  Retrying in {wait_time} seconds...")
                time.sleep(wait_time)
            else:
                print(f"  All {max_retries} attempts failed: {e}")
                return pd.DataFrame()  # Return empty dataframe after all retries fail
    return pd.DataFrame()

# Process each team separately
for team in nba_teams:
    team_name_clean = team['name'].replace(' ', '_').replace('.', '')
    team_file = raw_data_dir / f"nba_{team_name_clean}_{team['api_id']}.csv"

    # Skip if team file already exists
    if team_file.exists():
        print(f"\n=== Skipping {team['name']} (file already exists) ===")
        continue

    print(f"\n=== Fetching data for {team['name']} (ID: {team['api_id']}) ===")
    team_games_list = []

    for i in range(2000, 2026):
        season_str = f"{i}-{str(i+1)[-2:]}"
        print(f"Fetching season {season_str}...")

        for season_type in season_types:
            games = fetch_with_retry(season_str, season_type, team['api_id'])

            if not games.empty:
                games['SEASON'] = season_str
                team_games_list.append(games)
                print(f"  Fetched {season_type} with {games.shape[0]} games.")

            # Rate limiting: wait between requests
            time.sleep(1.0)  # Increased from 0.6 to 1.0 second

    # Save team data to individual file
    if team_games_list:
        team_games = pd.concat(team_games_list, ignore_index=True)
        team_games.to_csv(team_file, index=False)
        print(f"Saved {len(team_games)} games for {team['name']} to {team_file}")
    else:
        print(f"No games fetched for {team['name']}")

print("\n=== All teams processed ===")
print(f"Individual team files saved to: {raw_data_dir}")

# Combine all team files into single dataset
# print("\nCombining all team files into single dataset...")
# all_team_files = list(raw_data_dir.glob("nba_*.csv"))
# if all_team_files:
#     all_games = pd.concat([pd.read_csv(f) for f in all_team_files], ignore_index=True)
#     all_games.to_csv(config.NBA_ALL_GAMES, index=False)
#     print(f"All NBA games data saved to: {config.NBA_ALL_GAMES}")
