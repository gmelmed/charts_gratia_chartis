import pandas as pd
import time
import sys
import json
from pathlib import Path

# Add parent directory to path to import config
sys.path.insert(0, str(Path(__file__).parent.parent))
import config

# MLB-StatsAPI package (pip install MLB-StatsAPI)
import statsapi

# Load markets_teams.json
markets_teams_path = Path(__file__).parent.parent / "data" / "markets_teams.json"
with open(markets_teams_path, 'r') as f:
    markets_data = json.load(f)

# Create output directory if it doesn't exist
output_dir = Path(__file__).parent.parent / "data" / "raw" / "mlb"
output_dir.mkdir(parents=True, exist_ok=True)

# Extract all MLB teams
mlb_teams = []
for market in markets_data['markets_teams']:
    for team in market['teams']:
        if team['league'] == 'MLB':
            mlb_teams.append({
                'market': market['market'],
                'name': team['name'],
                'api_id': team['api_id']
            })

print(f"Found {len(mlb_teams)} MLB teams to fetch")

# Loop through each MLB team
for team_info in mlb_teams:
    market = team_info['market'].lower()
    team_name = team_info['name']
    team_id = team_info['api_id']

    # Create safe filename from team name (remove spaces and special chars)
    team_filename = team_name.lower().replace(' ', '_').replace('.', '')
    
    # skip if team file already exists
    output_file = output_dir / f"mlb_{market}_{team_filename}_games.csv"
    if output_file.exists():
        print(f"\n=== Data for {team_name} already exists. Skipping. ===")
        continue

    print(f"\n{'='*60}")
    print(f"Fetching games for {team_name} (ID: {team_id})")
    print(f"{'='*60}")

    all_games_list = []
    for year in range(2000, 2026):
        print(f"  Season {year}...", end=" ")

        # Retry logic with exponential backoff
        max_retries = 3
        retry_delay = 2

        for attempt in range(max_retries):
            try:
                # Fetch games for specific team
                games = statsapi.schedule(start_date=f"{year}-03-01", end_date=f"{year}-11-30", team=team_id)
                games_df = pd.DataFrame(games)
                games_df['SEASON'] = year
                all_games_list.append(games_df)
                print(f"{games_df.shape[0]} games")

                # Success - break out of retry loop
                break

            except Exception as e:
                if attempt < max_retries - 1:
                    wait_time = retry_delay * (2 ** attempt)
                    print(f"\n    Error (attempt {attempt + 1}/{max_retries}): {e}")
                    print(f"    Retrying in {wait_time} seconds...")
                    time.sleep(wait_time)
                else:
                    print(f"\n    Failed after {max_retries} attempts: {e}")
                    continue

        # Rate limiting: wait between requests
        time.sleep(1.5)

    # Combine all seasons for this team
    if all_games_list:
        team_games = pd.concat(all_games_list, ignore_index=True)

        # Save to CSV
        output_file = output_dir / f"mlb_{market}_{team_filename}_games.csv"
        team_games.to_csv(output_file, index=False)
        print(f"\nSaved {team_games.shape[0]} total games to: {output_file.name}")
    else:
        print(f"\nNo games found for {team_name}")

print(f"\n{'='*60}")
print("All MLB team data saved!")
print(f"{'='*60}")