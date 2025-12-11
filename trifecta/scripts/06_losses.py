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
# Use market_name format to avoid collisions (e.g., bay_giants for SF Giants, ny_giants for NY Giants)
team_to_league = {}
for team in mlb_teams:
    market_name = team['market'].lower()
    team_name = team['name'].lower().replace(' ', '_').replace('-', '_')
    team_to_league[f'{market_name}_{team_name}_loss'] = 'MLB'
for team in nhl_teams:
    market_name = team['market'].lower()
    team_name = team['name'].lower().replace(' ', '_').replace('-', '_')
    team_to_league[f'{market_name}_{team_name}_loss'] = 'NHL'
for team in nba_teams:
    market_name = team['market'].lower()
    team_name = team['name'].lower().replace(' ', '_').replace('-', '_')
    team_to_league[f'{market_name}_{team_name}_loss'] = 'NBA'
for team in nfl_teams:
    market_name = team['market'].lower()
    team_name = team['name'].lower().replace(' ', '_').replace('-', '_')
    team_to_league[f'{market_name}_{team_name}_loss'] = 'NFL'


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
    market_losses_df = None

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

        # create a col in the cleaned df indicating if the team lost
        # Use market_teamname format to avoid collisions (e.g., bay_giants vs ny_giants)
        col_name = f'{market_lower}_{team_name}_loss'
        df_cleaned[col_name] = (df_cleaned['losing_team'] == team_full_name).astype(int)

        # Create team losses dataframe
        team_losses = df_cleaned[['game_date', col_name]].copy()

        # Merge with market losses dataframe
        if market_losses_df is None:
            market_losses_df = team_losses.rename(columns={'game_date': 'date'})
        else:
            market_losses_df = market_losses_df.merge(
                team_losses.rename(columns={'game_date': 'date'}),
                on='date',
                how='outer'
            )

    # Fill NaN values with 0 (days when team didn't play)
    if market_losses_df is not None:
        market_losses_df = market_losses_df.fillna(0)
        market_losses_df = market_losses_df.sort_values('date').reset_index(drop=True)

        # Add total_losses and losing_teams columns
        loss_cols = [col for col in market_losses_df.columns if col.endswith('_loss')]
        market_losses_df['total_losses'] = market_losses_df[loss_cols].sum(axis=1)

        def get_losing_teams(row):
            losers = []
            for col in loss_cols:
                if row[col] == 1:
                    # Extract team name from column (e.g., 'bay_giants_loss' -> 'Giants')
                    # Remove market prefix and _loss suffix
                    team_name = col.replace('_loss', '')
                    # Remove the market prefix (e.g., 'bay_giants' -> 'giants')
                    if '_' in team_name:
                        team_name = '_'.join(team_name.split('_')[1:])
                    team_name = team_name.replace('_', ' ').title()
                    losers.append(team_name)
            return losers

        def get_losing_leagues(row):
            leagues = []
            for col in loss_cols:
                if row[col] == 1 and col in team_to_league:
                    league = team_to_league[col]
                    if league not in leagues:
                        leagues.append(league)
            return leagues

        market_losses_df['losing_teams'] = market_losses_df.apply(get_losing_teams, axis=1)
        market_losses_df['losing_leagues'] = market_losses_df.apply(get_losing_leagues, axis=1)
        market_losses_df['num_leagues_with_losses'] = market_losses_df['losing_leagues'].apply(len)

        # Save the dataframe to a variable
        globals()[f'{market_lower}_losses'] = market_losses_df


def clean_nhl_data(df):
    """Clean NHL data."""
    # Convert game_date to datetime
    df['game_date'] = pd.to_datetime(df['game_date'])

    # Determine losing team based on scores
    # If home_score > away_score, away team lost; otherwise home team lost
    df['losing_team'] = df.apply(
        lambda row: row['away_team_abbr'] if row['home_score'] > row['away_score'] else row['home_team_abbr'],
        axis=1
    )

    return df

# Group NHL teams by market
market_teams_dict_nhl = defaultdict(list)
for team in nhl_teams:
    market_teams_dict_nhl[team['market']].append(team)

# Process each team in the market
for market, teams in market_teams_dict_nhl.items():
    market_lower = market.lower()
    nhl_market_losses_df = None

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

        # create a col in the cleaned df indicating if the team lost
        # Use market_teamname format to avoid collisions
        col_name = f'{market_lower}_{team_name}_loss'
        df_cleaned[col_name] = (df_cleaned['losing_team'] == team_abbr).astype(int)

        # Create team losses dataframe
        team_losses = df_cleaned[['game_date', col_name]].copy()

        # Merge with NHL market losses dataframe
        team_losses = team_losses.rename(columns={'game_date': 'date'})
        if nhl_market_losses_df is None:
            nhl_market_losses_df = team_losses
        else:
            nhl_market_losses_df = nhl_market_losses_df.merge(
                team_losses,
                on='date',
                how='outer'
            )

    # Merge NHL data with existing market_losses dataframe
    if nhl_market_losses_df is not None:
        # Check if existing data exists for this market
        if f'{market_lower}_losses' in globals():
            existing_df = globals()[f'{market_lower}_losses']
            # Remove old total_losses and losing_teams columns if they exist
            if 'total_losses' in existing_df.columns:
                existing_df = existing_df.drop(columns=['total_losses', 'losing_teams', 'losing_leagues', 'num_leagues_with_losses'])
            # Merge existing and NHL data
            combined_df = existing_df.merge(
                nhl_market_losses_df,
                on='date',
                how='outer'
            )
            # Fill NaN values with 0
            combined_df = combined_df.fillna(0)
            combined_df = combined_df.sort_values('date').reset_index(drop=True)

            # Add total_losses and losing_teams columns
            loss_cols = [col for col in combined_df.columns if col.endswith('_loss')]
            combined_df['total_losses'] = combined_df[loss_cols].sum(axis=1)

            def get_losing_teams(row):
                losers = []
                for col in loss_cols:
                    if row[col] == 1:
                        # Extract team name from column (e.g., 'bay_giants_loss' -> 'Giants')
                        team_name = col.replace('_loss', '')
                        # Remove the market prefix
                        if '_' in team_name:
                            team_name = '_'.join(team_name.split('_')[1:])
                        team_name = team_name.replace('_', ' ').title()
                        losers.append(team_name)
                return losers

            def get_losing_leagues(row):
                leagues = []
                for col in loss_cols:
                    if row[col] == 1 and col in team_to_league:
                        league = team_to_league[col]
                        if league not in leagues:
                            leagues.append(league)
                return leagues

            combined_df['losing_teams'] = combined_df.apply(get_losing_teams, axis=1)
            combined_df['losing_leagues'] = combined_df.apply(get_losing_leagues, axis=1)
            combined_df['num_leagues_with_losses'] = combined_df['losing_leagues'].apply(len)
            globals()[f'{market_lower}_losses'] = combined_df


def clean_nba_data(df, team_abbr):
    """Clean NBA data."""
    # Filter for team games only
    df = df[df['TEAM_ABBREVIATION'] == team_abbr].copy()

    # Convert GAME_DATE to datetime
    df['date'] = pd.to_datetime(df['GAME_DATE'])

    # Select relevant columns
    df = df[['date', 'WL']].copy()

    return df

# Group NBA teams by market
market_teams_dict_nba = defaultdict(list)
for team in nba_teams:
    market_teams_dict_nba[team['market']].append(team)

# Process each team in the market
for market, teams in market_teams_dict_nba.items():
    market_lower = market.lower()
    nba_market_losses_df = None

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

        # create a col in the cleaned df indicating if the team lost
        # Use market_teamname format to avoid collisions
        col_name = f'{market_lower}_{team_name}_loss'
        df_cleaned[col_name] = (df_cleaned['WL'] == 'L').astype(int)

        # Create team losses dataframe
        team_losses = df_cleaned[['date', col_name]].copy()

        # Merge with NBA market losses dataframe
        if nba_market_losses_df is None:
            nba_market_losses_df = team_losses
        else:
            nba_market_losses_df = nba_market_losses_df.merge(
                team_losses,
                on='date',
                how='outer'
            )

    # Merge NBA data with existing market_losses dataframe
    if nba_market_losses_df is not None:
        # Check if existing data exists for this market
        if f'{market_lower}_losses' in globals():
            existing_df = globals()[f'{market_lower}_losses']
            # Remove old total_losses and losing_teams columns if they exist
            if 'total_losses' in existing_df.columns:
                existing_df = existing_df.drop(columns=['total_losses', 'losing_teams', 'losing_leagues', 'num_leagues_with_losses'])
            # Merge existing and NBA data
            combined_df = existing_df.merge(
                nba_market_losses_df,
                on='date',
                how='outer'
            )
            # Fill NaN values with 0
            combined_df = combined_df.fillna(0)
            combined_df = combined_df.sort_values('date').reset_index(drop=True)

            # Add total_losses and losing_teams columns
            loss_cols = [col for col in combined_df.columns if col.endswith('_loss')]
            combined_df['total_losses'] = combined_df[loss_cols].sum(axis=1)

            def get_losing_teams(row):
                losers = []
                for col in loss_cols:
                    if row[col] == 1:
                        # Extract team name from column (e.g., 'bay_giants_loss' -> 'Giants')
                        team_name = col.replace('_loss', '')
                        # Remove the market prefix
                        if '_' in team_name:
                            team_name = '_'.join(team_name.split('_')[1:])
                        team_name = team_name.replace('_', ' ').title()
                        losers.append(team_name)
                return losers

            def get_losing_leagues(row):
                leagues = []
                for col in loss_cols:
                    if row[col] == 1 and col in team_to_league:
                        league = team_to_league[col]
                        if league not in leagues:
                            leagues.append(league)
                return leagues

            combined_df['losing_teams'] = combined_df.apply(get_losing_teams, axis=1)
            combined_df['losing_leagues'] = combined_df.apply(get_losing_leagues, axis=1)
            combined_df['num_leagues_with_losses'] = combined_df['losing_leagues'].apply(len)
            globals()[f'{market_lower}_losses'] = combined_df


# process nfl data
# group teams by market
market_teams_dict_nfl = defaultdict(list)
for team in nfl_teams:
    market_teams_dict_nfl[team['market']].append(team)

# Process each team in the market
for market, teams in market_teams_dict_nfl.items():
    market_lower = market.lower()
    nfl_market_losses_df = None

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


        df['losing_team'] = df.apply(lambda row: row['away_team'] if row['home_score'] > row['away_score'] else row['home_team'], axis=1)

        # create a col in the cleaned df indicating if the team lost
        # Use market_teamname format to avoid collisions
        col_name = f'{market_lower}_{team_name}_loss'
        df[col_name] = (df['losing_team'] == team_abbr).astype(int)

        # Create team losses dataframe
        team_losses = df[['date', col_name]].copy()

        # Merge with NFL market losses dataframe
        if nfl_market_losses_df is None:
            nfl_market_losses_df = team_losses
        else:
            nfl_market_losses_df = nfl_market_losses_df.merge(
                team_losses,
                on='date',
                how='outer'
            )

    # Merge NFL data with existing market_losses dataframe
    if nfl_market_losses_df is not None:
        # Check if existing data exists for this market
        if f'{market_lower}_losses' in globals():
            existing_df = globals()[f'{market_lower}_losses']
            # Remove old total_losses and losing_teams columns if they exist
            if 'total_losses' in existing_df.columns:
                existing_df = existing_df.drop(columns=['total_losses', 'losing_teams', 'losing_leagues', 'num_leagues_with_losses'])
            # Merge existing and NFL data
            combined_df = existing_df.merge(
                nfl_market_losses_df,
                on='date',
                how='outer'
            )
            # Fill NaN values with 0
            combined_df = combined_df.fillna(0)
            combined_df = combined_df.sort_values('date').reset_index(drop=True)

            # Add total_losses and losing_teams columns
            loss_cols = [col for col in combined_df.columns if col.endswith('_loss')]
            combined_df['total_losses'] = combined_df[loss_cols].sum(axis=1)

            def get_losing_teams(row):
                losers = []
                for col in loss_cols:
                    if row[col] == 1:
                        # Extract team name from column (e.g., 'bay_giants_loss' -> 'Giants')
                        team_name = col.replace('_loss', '')
                        # Remove the market prefix
                        if '_' in team_name:
                            team_name = '_'.join(team_name.split('_')[1:])
                        team_name = team_name.replace('_', ' ').title()
                        losers.append(team_name)
                return losers

            def get_losing_leagues(row):
                leagues = []
                for col in loss_cols:
                    if row[col] == 1 and col in team_to_league:
                        league = team_to_league[col]
                        if league not in leagues:
                            leagues.append(league)
                return leagues

            combined_df['losing_teams'] = combined_df.apply(get_losing_teams, axis=1)
            combined_df['losing_leagues'] = combined_df.apply(get_losing_leagues, axis=1)
            combined_df['num_leagues_with_losses'] = combined_df['losing_leagues'].apply(len)
            globals()[f'{market_lower}_losses'] = combined_df

# Save all market dataframes to CSV
output_dir = script_dir.parent / "data" / "processed"
output_dir.mkdir(parents=True, exist_ok=True)

# Get list of variable names ending with '_losses' before iterating
losses_vars = [var_name for var_name in list(globals().keys()) if var_name.endswith('_losses')]

for var_name in losses_vars:
    df = globals()[var_name]
    output_file = output_dir / f"{var_name}.csv"
    df.to_csv(output_file, index=False)

print("Data cleaning and combining complete.")