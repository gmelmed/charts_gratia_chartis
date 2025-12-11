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
            
            
# get nhl teams
nhl_teams = []
for market in markets_data['markets_teams']:
    for team in market['teams']:
        if team['league'] == 'NHL':
            nhl_teams.append({
                'market': market['market'],
                'name': team['name'],
                'api_id': team['api_id'],
                'abbr': team['abbr'],
                'full_name': team['full_name']
            })

nba_teams = []
for market in markets_data['markets_teams']:
    for team in market['teams']:
        if team['league'] == 'NBA':
            nba_teams.append({
                'market': market['market'],
                'name': team['name'],
                'api_id': team['api_id'],
                'abbr': team['abbr'],
                'full_name': team['full_name']
            })
            
            
nfl_teams = []
for market in markets_data['markets_teams']:
    for team in market['teams']:
        if team['league'] == 'NFL':
            nfl_teams.append({
                'market': market['market'],
                'name': team['name'],
                'api_id': team['api_id'],
                'abbr': team['abbr'],
                'full_name': team['full_name']
            })

# Create a mapping of team column names to leagues
team_to_league = {}
for team in mlb_teams:
    team_name = team['name'].lower().replace(' ', '_').replace('-', '_')
    team_to_league[f'{team_name}_win'] = 'MLB'
for team in nhl_teams:
    team_name = team['name'].lower().replace(' ', '_').replace('-', '_')
    team_to_league[f'{team_name}_win'] = 'NHL'
for team in nba_teams:
    team_name = team['name'].lower().replace(' ', '_').replace('-', '_')
    team_to_league[f'{team_name}_win'] = 'NBA'
for team in nfl_teams:
    team_name = team['name'].lower().replace(' ', '_').replace('-', '_')
    team_to_league[f'{team_name}_win'] = 'NFL'


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

# Group teams by market
from collections import defaultdict
market_teams_dict = defaultdict(list)
for team in mlb_teams:
    market_teams_dict[team['market']].append(team)

# Process each market
for market, teams in market_teams_dict.items():
    market_lower = market.lower()
    market_wins_df = None

    # Process each team in the market
    for team in teams:
        team_name = team['name'].lower().replace(' ', '_').replace('-', '_')
        team_abbr = team['abbr']
        team_full_name = team['full_name']

        input_file = script_dir.parent / "data" / "raw" / "mlb" / f"mlb_{market_lower}_{team_name}_games.csv"

        if not input_file.exists():
            print(f"  Input file {input_file} does not exist. Skipping.")
            continue

        df = pd.read_csv(input_file)
        df_cleaned = clean_mlb_data(df)

        # Filter out pre-2005 data for Washington Nationals (Montreal Expos era)
        if team_full_name == 'Washington Nationals':
            df_cleaned = df_cleaned[df_cleaned['game_date'].dt.year >= 2005].copy()

        # create a col in the cleaned df indicating if the team won
        df_cleaned[f'{team_name}_win'] = (df_cleaned['winning_team'] == team_full_name).astype(int)

        # Create team wins dataframe
        team_wins = df_cleaned[['game_date', f'{team_name}_win']].copy()

        # Merge with market wins dataframe
        if market_wins_df is None:
            market_wins_df = team_wins.rename(columns={'game_date': 'date'})
        else:
            market_wins_df = market_wins_df.merge(
                team_wins.rename(columns={'game_date': 'date'}),
                on='date',
                how='outer'
            )

    # Fill NaN values with 0 (days when team didn't play)
    if market_wins_df is not None:
        market_wins_df = market_wins_df.fillna(0)
        market_wins_df = market_wins_df.sort_values('date').reset_index(drop=True)

        # Add total_wins and winning_teams columns
        win_cols = [col for col in market_wins_df.columns if col.endswith('_win')]
        market_wins_df['total_wins'] = market_wins_df[win_cols].sum(axis=1)

        def get_winning_teams(row):
            winners = []
            for col in win_cols:
                if row[col] == 1:
                    # Extract team name from column (e.g., 'yankees_win' -> 'Yankees')
                    team_name = col.replace('_win', '').replace('_', ' ').title()
                    winners.append(team_name)
            return winners

        def get_winning_leagues(row):
            leagues = []
            for col in win_cols:
                if row[col] == 1 and col in team_to_league:
                    league = team_to_league[col]
                    if league not in leagues:
                        leagues.append(league)
            return leagues

        market_wins_df['winning_teams'] = market_wins_df.apply(get_winning_teams, axis=1)
        market_wins_df['winning_leagues'] = market_wins_df.apply(get_winning_leagues, axis=1)

        # Assign to a variable named {market}_wins
        globals()[f'{market_lower}_wins'] = market_wins_df
        
def clean_nhl_data(df):
    # Select relevant columns
    df = df[['game_date', 'home_team_abbr', 'away_team_abbr', 'home_score',
       'away_score']].copy()

    # Convert game_date to datetime
    df['game_date'] = pd.to_datetime(df['game_date'])
    
    df = df.rename(columns={'game_date': 'date'})
    
    df['winning_team'] = df.apply(lambda row: row['home_team_abbr'] if row['home_score'] > row['away_score'] else row['away_team_abbr'], axis=1)
    
    return df

# Group teams by market
market_teams_dict_nhl = defaultdict(list)
for team in nhl_teams:
    market_teams_dict_nhl[team['market']].append(team)

# Process each market
for market, teams in market_teams_dict_nhl.items():
    market_lower = market.lower()
    nhl_market_wins_df = None

    # Process each team in the market
    for team in teams:
        team_name = team['name'].lower().replace(' ', '_').replace('-', '_')
        team_abbr = team['abbr']
        team_full_name = team['full_name']

        input_file = script_dir.parent / "data" / "raw" / "nhl" / f"nhl_{market_lower}_{team_name}_games.csv"

        if not input_file.exists():
            print(f"  Input file {input_file} does not exist. Skipping.")
            continue

        df = pd.read_csv(input_file)
        df_cleaned = clean_nhl_data(df)

        # create a col in the cleaned df indicating if the team won
        df_cleaned[f'{team_name}_win'] = (df_cleaned['winning_team'] == team_abbr).astype(int)

        # Create team wins dataframe
        team_wins = df_cleaned[['date', f'{team_name}_win']].copy()

        # Merge with NHL market wins dataframe
        if nhl_market_wins_df is None:
            nhl_market_wins_df = team_wins
        else:
            nhl_market_wins_df = nhl_market_wins_df.merge(
                team_wins,
                on='date',
                how='outer'
            )

    # Merge NHL data with existing MLB market_wins dataframe
    if nhl_market_wins_df is not None:
        # Check if MLB data exists for this market
        if f'{market_lower}_wins' in globals():
            existing_df = globals()[f'{market_lower}_wins']
            # Remove old total_wins and winning_teams columns if they exist
            if 'total_wins' in existing_df.columns:
                existing_df = existing_df.drop(columns=['total_wins', 'winning_teams', 'winning_leagues'])
            # Merge MLB and NHL data
            combined_df = existing_df.merge(
                nhl_market_wins_df,
                on='date',
                how='outer'
            )
            # Fill NaN values with 0
            combined_df = combined_df.fillna(0)
            combined_df = combined_df.sort_values('date').reset_index(drop=True)

            # Add total_wins and winning_teams columns
            win_cols = [col for col in combined_df.columns if col.endswith('_win')]
            combined_df['total_wins'] = combined_df[win_cols].sum(axis=1)

            def get_winning_teams(row):
                winners = []
                for col in win_cols:
                    if row[col] == 1:
                        team_name = col.replace('_win', '').replace('_', ' ').title()
                        winners.append(team_name)
                return winners

            def get_winning_leagues(row):
                leagues = []
                for col in win_cols:
                    if row[col] == 1 and col in team_to_league:
                        league = team_to_league[col]
                        if league not in leagues:
                            leagues.append(league)
                return leagues

            combined_df['winning_teams'] = combined_df.apply(get_winning_teams, axis=1)
            combined_df['winning_leagues'] = combined_df.apply(get_winning_leagues, axis=1)
            globals()[f'{market_lower}_wins'] = combined_df
        else:
            # No MLB data for this market, just use NHL data
            nhl_market_wins_df = nhl_market_wins_df.fillna(0)
            nhl_market_wins_df = nhl_market_wins_df.sort_values('date').reset_index(drop=True)

            # Add total_wins and winning_teams columns
            win_cols = [col for col in nhl_market_wins_df.columns if col.endswith('_win')]
            nhl_market_wins_df['total_wins'] = nhl_market_wins_df[win_cols].sum(axis=1)

            def get_winning_teams(row):
                winners = []
                for col in win_cols:
                    if row[col] == 1:
                        team_name = col.replace('_win', '').replace('_', ' ').title()
                        winners.append(team_name)
                return winners

            def get_winning_leagues(row):
                leagues = []
                for col in win_cols:
                    if row[col] == 1 and col in team_to_league:
                        league = team_to_league[col]
                        if league not in leagues:
                            leagues.append(league)
                return leagues

            nhl_market_wins_df['winning_teams'] = nhl_market_wins_df.apply(get_winning_teams, axis=1)
            nhl_market_wins_df['winning_leagues'] = nhl_market_wins_df.apply(get_winning_leagues, axis=1)
            globals()[f'{market_lower}_wins'] = nhl_market_wins_df


# process nba data
# Group teams by market
market_teams_dict_nba = defaultdict(list)
for team in nba_teams:
    market_teams_dict_nba[team['market']].append(team)
    
    
def clean_nba_data(df, team_abbr):
    # Select relevant columns
    df = df[['GAME_DATE', 'TEAM_ABBREVIATION', 'WL']].copy()

    # Convert game_date to datetime
    df['GAME_DATE'] = pd.to_datetime(df['GAME_DATE'])

    df = df.rename(columns={'GAME_DATE': 'date'})

    # Filter to only include rows where TEAM_ABBREVIATION matches the current team
    df = df[df['TEAM_ABBREVIATION'] == team_abbr].copy()

    return df

# Process each market
for market, teams in market_teams_dict_nba.items():
    market_lower = market.lower()
    nba_market_wins_df = None

    # Process each team in the market
    for team in teams:
        team_name = team['name'].lower().replace(' ', '_').replace('-', '_')
        team_abbr = team['abbr']
        team_full_name = team['full_name']

        input_file = script_dir.parent / "data" / "raw" / "nba" / f"nba_{market_lower}_{team_name}_games.csv"

        if not input_file.exists():
            print(f"  Input file {input_file} does not exist. Skipping.")
            continue

        df = pd.read_csv(input_file)
        df_cleaned = clean_nba_data(df, team_abbr)

        # create a col in the cleaned df indicating if the team won
        df_cleaned[f'{team_name}_win'] = (df_cleaned['WL'] == 'W').astype(int)

        # Create team wins dataframe
        team_wins = df_cleaned[['date', f'{team_name}_win']].copy()

        # Merge with NBA market wins dataframe
        if nba_market_wins_df is None:
            nba_market_wins_df = team_wins
        else:
            nba_market_wins_df = nba_market_wins_df.merge(
                team_wins,
                on='date',
                how='outer'
            )

    # Merge NBA data with existing market_wins dataframe
    if nba_market_wins_df is not None:
        # Check if existing data exists for this market
        if f'{market_lower}_wins' in globals():
            existing_df = globals()[f'{market_lower}_wins']
            # Remove old total_wins and winning_teams columns if they exist
            if 'total_wins' in existing_df.columns:
                existing_df = existing_df.drop(columns=['total_wins', 'winning_teams', 'winning_leagues'])
            # Merge existing and NBA data
            combined_df = existing_df.merge(
                nba_market_wins_df,
                on='date',
                how='outer'
            )
            # Fill NaN values with 0
            combined_df = combined_df.fillna(0)
            combined_df = combined_df.sort_values('date').reset_index(drop=True)

            # Add total_wins and winning_teams columns
            win_cols = [col for col in combined_df.columns if col.endswith('_win')]
            combined_df['total_wins'] = combined_df[win_cols].sum(axis=1)

            def get_winning_teams(row):
                winners = []
                for col in win_cols:
                    if row[col] == 1:
                        team_name = col.replace('_win', '').replace('_', ' ').title()
                        winners.append(team_name)
                return winners

            def get_winning_leagues(row):
                leagues = []
                for col in win_cols:
                    if row[col] == 1 and col in team_to_league:
                        league = team_to_league[col]
                        if league not in leagues:
                            leagues.append(league)
                return leagues

            combined_df['winning_teams'] = combined_df.apply(get_winning_teams, axis=1)
            combined_df['winning_leagues'] = combined_df.apply(get_winning_leagues, axis=1)
            globals()[f'{market_lower}_wins'] = combined_df


# process nfl data
# group teams by market
market_teams_dict_nfl = defaultdict(list)
for team in nfl_teams:
    market_teams_dict_nfl[team['market']].append(team)

# Process each team in the market
for market, teams in market_teams_dict_nfl.items():
    market_lower = market.lower()
    nfl_market_wins_df = None

    # Process each team in the market
    for team in teams:
        team_name = team['name'].lower().replace(' ', '_').replace('-', '_')
        team_abbr = team['abbr']
        team_full_name = team['full_name']

        input_file = script_dir.parent / "data" / "raw" / "nfl" / f"nfl_{market_lower}_{team_name}_games.csv"

        if not input_file.exists():
            print(f"  Input file {input_file} does not exist. Skipping.")
            continue

        df = pd.read_csv(input_file)
        # clean nfl data
        df['date'] = pd.to_datetime(df['gameday'])
        
        
        df['winning_team'] = df.apply(lambda row: row['home_team'] if row['home_score'] > row['away_score'] else row['away_team'], axis=1)

        # create a col in the cleaned df indicating if the team won
        df[f'{team_name}_win'] = (df['winning_team'] == team_abbr).astype(int)

        # Create team wins dataframe
        team_wins = df[['date', f'{team_name}_win']].copy()

        # Merge with NFL market wins dataframe
        if nfl_market_wins_df is None:
            nfl_market_wins_df = team_wins
        else:
            nfl_market_wins_df = nfl_market_wins_df.merge(
                team_wins,
                on='date',
                how='outer'
            )

    # Merge NFL data with existing market_wins dataframe
    if nfl_market_wins_df is not None:
        # Check if existing data exists for this market
        if f'{market_lower}_wins' in globals():
            existing_df = globals()[f'{market_lower}_wins']
            # Remove old total_wins and winning_teams columns if they exist
            if 'total_wins' in existing_df.columns:
                existing_df = existing_df.drop(columns=['total_wins', 'winning_teams', 'winning_leagues'])
            # Merge existing and NFL data
            combined_df = existing_df.merge(
                nfl_market_wins_df,
                on='date',
                how='outer'
            )
            # Fill NaN values with 0
            combined_df = combined_df.fillna(0)
            combined_df = combined_df.sort_values('date').reset_index(drop=True)

            # Add total_wins and winning_teams columns
            win_cols = [col for col in combined_df.columns if col.endswith('_win')]
            combined_df['total_wins'] = combined_df[win_cols].sum(axis=1)

            def get_winning_teams(row):
                winners = []
                for col in win_cols:
                    if row[col] == 1:
                        team_name = col.replace('_win', '').replace('_', ' ').title()
                        winners.append(team_name)
                return winners

            def get_winning_leagues(row):
                leagues = []
                for col in win_cols:
                    if row[col] == 1 and col in team_to_league:
                        league = team_to_league[col]
                        if league not in leagues:
                            leagues.append(league)
                return leagues

            combined_df['winning_teams'] = combined_df.apply(get_winning_teams, axis=1)
            combined_df['winning_leagues'] = combined_df.apply(get_winning_leagues, axis=1)
            globals()[f'{market_lower}_wins'] = combined_df

# Save all market dataframes to CSV
output_dir = script_dir.parent / "data" / "processed"
output_dir.mkdir(parents=True, exist_ok=True)

# Get list of variable names ending with '_wins' before iterating
wins_vars = [var_name for var_name in list(globals().keys()) if var_name.endswith('_wins')]

for var_name in wins_vars:
    df = globals()[var_name]
    output_file = output_dir / f"{var_name}.csv"
    df.to_csv(output_file, index=False)

print("Data cleaning and combining complete.")    