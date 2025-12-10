import pandas as pd
import time
import sys
import json
from pathlib import Path

# Add parent directory to path to import config
sys.path.insert(0, str(Path(__file__).parent.parent))
import config
from nhlpy.nhl_client import NHLClient

client = NHLClient()

# Load markets_teams.json
markets_teams_path = Path(__file__).parent.parent / "data" / "markets_teams.json"
with open(markets_teams_path, 'r') as f:
    markets_data = json.load(f)

# Create output directory if it doesn't exist
output_dir = Path(__file__).parent.parent / "data" / "raw" / "nhl"
output_dir.mkdir(parents=True, exist_ok=True)

# Extract all NHL teams
nhl_teams = []
for market in markets_data['markets_teams']:
    for team in market['teams']:
        if team['league'] == 'NHL':
            nhl_teams.append({
                'market': market['market'],
                'name': team['name'],
                'api_id': team['api_id']
            })

print(f"Found {len(nhl_teams)} NHL teams to fetch")


# Create a mapping from team names to abbreviations (cache this to avoid repeated API calls)
print("Fetching team abbreviations...")
teams_data = client.teams.teams()
name_to_abbr = {}
for team in teams_data:
    common_name = team.get('common_name', '')
    abbr = team.get('abbr', '')
    if common_name and abbr:
        name_to_abbr[common_name] = abbr

# Loop through each NHL team
for team_info in nhl_teams:
    market = team_info['market'].lower()
    team_name = team_info['name']
    team_id = team_info['api_id']

    # Create safe filename from team name (remove spaces and special chars)
    team_filename = team_name.lower().replace(' ', '_').replace('.', '')

    # Skip if team file already exists
    output_file = output_dir / f"nhl_{market}_{team_filename}_games.csv"
    if output_file.exists():
        print(f"\n=== Data for {team_name} already exists. Skipping. ===")
        continue

    print(f"\n{'='*60}")
    print(f"Fetching games for {team_name} (ID: {team_id})")
    print(f"{'='*60}")

    # Get team abbreviation
    team_abbr = name_to_abbr.get(team_name, None)
    if not team_abbr:
        print(f"  Warning: No abbreviation found for {team_name}. Skipping.")
        continue

    all_games_list = []
    for year in range(2000, 2026):
        season_str = f"{year}{year+1}"
        print(f"  Season {season_str}...", end=" ")

        # Retry logic with exponential backoff
        max_retries = 3
        retry_delay = 2

        for attempt in range(max_retries):
            try:
                # Fetch games for specific team
                schedule_data = client.schedule.team_season_schedule(team_abbr, season_str)
                games = schedule_data.get('games', [])

                # Convert games to DataFrame
                games_list = []
                for game in games:
                    game_dict = {
                        'game_date': game.get('gameDate'),
                        'home_team_abbr': game.get('homeTeam', {}).get('abbrev', ''),
                        'away_team_abbr': game.get('awayTeam', {}).get('abbrev', ''),
                        'home_score': game.get('homeTeam', {}).get('score'),
                        'away_score': game.get('awayTeam', {}).get('score'),
                    }
                    games_list.append(game_dict)

                games_df = pd.DataFrame(games_list)
                games_df['SEASON'] = season_str
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
        time.sleep(0.5)

    # Combine all seasons for this team
    if all_games_list:
        team_games = pd.concat(all_games_list, ignore_index=True)

        # Save to CSV
        output_file = output_dir / f"nhl_{market}_{team_filename}_games.csv"
        team_games.to_csv(output_file, index=False)
        print(f"\nSaved {team_games.shape[0]} total games to: {output_file.name}")
    else:
        print(f"\nNo games found for {team_name}")

print(f"\n{'='*60}")
print("All NHL team data saved!")
print(f"{'='*60}")