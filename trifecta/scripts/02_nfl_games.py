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

# Mapping of numeric API IDs to NFL abbreviations used by nfl_data_py
API_ID_TO_ABBR = {
    3800: 'ARI',  # Arizona Cardinals
    200: 'ATL',   # Atlanta Falcons
    325: 'BAL',   # Baltimore Ravens
    610: 'BUF',   # Buffalo Bills
    750: 'CAR',   # Carolina Panthers
    810: 'CHI',   # Chicago Bears
    920: 'CIN',   # Cincinnati Bengals
    1050: 'CLE',  # Cleveland Browns
    1200: 'DAL',  # Dallas Cowboys
    1400: 'DEN',  # Denver Broncos
    1540: 'DET',  # Detroit Lions
    1800: 'GB',   # Green Bay Packers
    2120: 'HOU',  # Houston Texans
    2200: 'IND',  # Indianapolis Colts
    2250: 'JAX',  # Jacksonville Jaguars
    2310: 'KC',   # Kansas City Chiefs
    2520: 'OAK',   # Oakland Raiders
    4400: 'LAC',  # Los Angeles Chargers
    2510: 'LA',   # Los Angeles Rams (also STL historically)
    2700: 'MIA',  # Miami Dolphins
    3000: 'MIN',  # Minnesota Vikings
    3200: 'NE',   # New England Patriots
    3300: 'NO',   # New Orleans Saints
    3410: 'NYG',  # New York Giants
    3430: 'NYJ',  # New York Jets
    3700: 'PHI',  # Philadelphia Eagles
    3900: 'PIT',  # Pittsburgh Steelers
    4500: 'SF',   # San Francisco 49ers
    4600: 'SEA',  # Seattle Seahawks
    4900: 'TB',   # Tampa Bay Buccaneers
    2100: 'TEN',  # Tennessee Titans
    5110: 'WAS',  # Washington Commanders
}

market_teams_path = Path(__file__).parent.parent / 'data' / 'markets_teams.json'
with open(market_teams_path, 'r') as f:
    markets_data = json.load(f)

nfl_teams = []
for market in markets_data['markets_teams']:
    for team in market['teams']:
        if team['league'] == 'NFL':
            team_abbr = API_ID_TO_ABBR.get(team['api_id'])
            if team_abbr:
                nfl_teams.append({
                    'name': team['name'],
                    'api_id': team['api_id'],
                    'abbr': team_abbr,
                    'market': market['market']
                })
            else:
                print(f"Warning: No abbreviation mapping found for {team['name']} (ID: {team['api_id']})")
                

                #   

# add the St. Louis Rams to the dictionary manually
nfl_teams.append({
    'name': 'St. Louis Rams',
    'api_id': 2520,
    'abbr': 'STL',
    'market': 'St Louis'
})

raw_data_dir = Path(__file__).parent.parent / 'data' / 'raw'
raw_data_dir.mkdir(parents=True, exist_ok=True)

print(f"Found {len(nfl_teams)} NFL teams to fetch data for")

def fetch_nfl_data(season, team_abbr):
    """Fetch NFL data for a given season and team."""
    try:
        # import_schedules returns all games for the season
        all_games = nfl.import_schedules([season])

        # Filter for games involving this team (either home or away)
        team_games = all_games[
            (all_games['home_team'] == team_abbr) |
            (all_games['away_team'] == team_abbr)
        ]
        return team_games
    except Exception as e:
        print(f"Error fetching data for team {team_abbr} in season {season}: {e}")
        return pd.DataFrame()

# Get all years from 2000 to present
years = list(range(2000, 2026))

for team in nfl_teams:
    print(f"\n=== Fetching data for team: {team['name']} ({team['abbr']}) ===")
    team_all_seasons = []
    for year in years:
        print(f"  Fetching season {year}...")
        season_data = fetch_nfl_data(year, team['abbr'])
        if not season_data.empty:
            team_all_seasons.append(season_data)
        time.sleep(0.5)

    if team_all_seasons:
        team_df = pd.concat(team_all_seasons, ignore_index=True)
        market_name = team['market'].lower().replace(' ', '_').replace('-', '_')
        team_name = team['name'].lower().replace(' ', '_')
        team_file_path = raw_data_dir / f"nfl_{market_name}_{team_name}_games.csv"
        team_df.to_csv(team_file_path, index=False)
        print(f"  Saved data for {team['name']} to {team_file_path}")
    else:
        print(f"  No data found for {team['name']}")

print("\n===ALL NFL TEAMS DATA FETCHED AND SAVED===")
print(f"Raw data directory: {raw_data_dir}")