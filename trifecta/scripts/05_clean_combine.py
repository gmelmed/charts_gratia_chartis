from anyio import Path
import pandas as pd
import os
import sys
from pathlib import Path

# Handle __file__ not being defined (e.g., in Jupyter notebooks)
try:
    script_dir = Path(__file__).parent
except NameError:
    script_dir = Path(os.getcwd()) / "scripts"

# Add parent directory to path to import config
sys.path.insert(0, str(script_dir.parent))
import config
import json

# Load markets_teams.json
markets_teams_path = script_dir.parent / "data" / "markets_teams.json"
with open(markets_teams_path, 'r') as f:
    markets_data = json.load(f)

mlb_teams = []
for market in markets_data['markets_teams']:
    for team in market['teams']:
        if team['league'] == 'MLB':
            mlb_teams.append({
                'market': market['market'],
                'name': team['name'],
                'api_id': team['api_id'],
                'abbr': team['abbr'],
                'full_name': team['full_name']
            })

def clean_mlb_data(df):
    """Clean MLB data."""
    # Select relevant columns
    df = df[['game_date', 'game_type', 'winning_team', 'losing_team']].copy()

    # Standardize team names
    df['winning_team'] = df['winning_team'].str.replace('Tampa Bay Devil Rays', 'Tampa Bay Rays', regex=False)
    df['losing_team'] = df['losing_team'].str.replace('Tampa Bay Devil Rays', 'Tampa Bay Rays', regex=False)
    df['winning_team'] = df['winning_team'].str.replace('Florida Marlins', 'Miami Marlins', regex=False)
    df['losing_team'] = df['losing_team'].str.replace('Florida Marlins', 'Miami Marlins', regex=False)
    df['winning_team'] = df['winning_team'].str.replace('Cleveland Indians', 'Cleveland Guardians', regex=False)
    df['losing_team'] = df['losing_team'].str.replace('Cleveland Indians', 'Cleveland Guardians', regex=False) 
    
    # Drop exhibition and spring training games
    df = df[~df['game_type'].isin(['E', 'S'])]
    
    # Convert game_date to datetime
    df['game_date'] = pd.to_datetime(df['game_date'])
    
    return df

for i in mlb_teams:
    market = i['market'].lower()
    team_name = i['name'].lower()
    team_abbr = i['abbr']
    team_full_name = i['full_name']

    input_file = script_dir.parent / "data" / "raw" / "mlb" / f"mlb_{market}_{team_name}.csv"
    print(f"\n{'='*60}")
    print(f"Processing data for {team_full_name}")
    if not input_file.exists():
        print(f"Input file {input_file} does not exist. Skipping.")
        continue
    
    df = pd.read_csv(input_file)
    df_cleaned = clean_mlb_data(df)
    
    # create a df



