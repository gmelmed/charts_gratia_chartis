import os
import time
import pandas as pd
from datetime import datetime
from nba_api.stats.static import teams
from nba_api.stats.endpoints import shotchartdetail


def get_all_shots_season(season='2025-26', delay=0.6, save_every=5):
    """
    Fetch all shot data for the specified season and save to CSV
    
    Parameters:
    - season: NBA season (e.g., '2025-26')
    - delay: Delay between API calls (seconds)
    - save_every: Save progress every N teams
    
    Returns:
    - DataFrame with all shot data
    """
    # Check if season already complete
    output_file = f'nba_shots_{season}_all.csv'
    if os.path.exists(output_file):
        print(f"✓ Season {season} already exists at {output_file}, skipping...")
        return pd.read_csv(output_file)
    
    # Get all teams
    all_teams = teams.get_teams()
    
    print(f"Starting shot data collection")
    print(f"Season: {season}")
    print(f"Total teams: {len(all_teams)}")
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("-" * 60)
    
    all_shots = []
    failed_teams = []
    
    for i, team in enumerate(all_teams, 1):
        team_id = team['id']
        team_name = team['full_name']
        
        try:
            # Fetch shot data for this team (all players on the team)
            shot_data = shotchartdetail.ShotChartDetail(
                team_id=team_id,
                player_id=0,  # 0 gets all players on the team
                context_measure_simple='FGA',
                season_nullable=season,
                season_type_all_star='Regular Season'
            )
            
            df = shot_data.get_data_frames()[0]
            
            if len(df) > 0:
                all_shots.append(df)
                print(f"[{i}/{len(all_teams)}] {team_name}: {len(df)} shots")
            else:
                print(f"[{i}/{len(all_teams)}] {team_name}: No shots")
            
            # Save progress periodically
            if i % save_every == 0 and all_shots:
                temp_df = pd.concat(all_shots, ignore_index=True)
                temp_df.to_csv(f'nba_shots_{season}_progress.csv', index=False)
                print(f"  → Progress saved: {len(temp_df)} total shots so far")
            
            # Rate limiting
            time.sleep(delay)
            
        except Exception as e:
            failed_teams.append((team_name, str(e)))
            print(f"[{i}/{len(all_teams)}] {team_name}: FAILED - {str(e)}")
            time.sleep(delay)
    
    print("-" * 60)
    print(f"Completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    if failed_teams:
        print(f"\nFailed to fetch data for {len(failed_teams)} teams:")
        for name, error in failed_teams:
            print(f"  - {name}: {error}")
    
    # Combine all shots
    if all_shots:
        combined_df = pd.concat(all_shots, ignore_index=True)
        print(f"\n✓ Total shots collected: {len(combined_df):,}")
        print(f"✓ Teams with shots: {len(all_shots)}")
        print(f"✓ Unique games: {combined_df.GAME_ID.nunique()}")
        print(f"✓ Unique players: {combined_df.PLAYER_NAME.nunique()}")
        
        # Save final dataset
        combined_df.to_csv(output_file, index=False)
        print(f"\n✓ Saved to: {output_file}")
        
        # Clean up progress file
        progress_file = f'nba_shots_{season}_progress.csv'
        if os.path.exists(progress_file):
            os.remove(progress_file)
        
        return combined_df
    else:
        print("\n✗ No shot data collected!")
        return pd.DataFrame()


def get_all_seasons(start_year=2000, end_year=2025, delay=0.6, save_every=5):
    """
    Fetch all shot data for multiple seasons
    
    Parameters:
    - start_year: First season year (e.g., 2000 for 2000-01)
    - end_year: Last season year (e.g., 2025 for 2025-26)
    - delay: Delay between API calls (seconds)
    - save_every: Save progress every N teams
    """
    overall_start = datetime.now()
    total_seasons = end_year - start_year + 1
    
    print(f"{'='*60}")
    print(f"FETCHING {total_seasons} SEASONS ({start_year}-{str(start_year-2000+1).zfill(2)} to {end_year}-{str(end_year-2000+1).zfill(2)})")
    print(f"Started at: {overall_start.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*60}\n")
    
    results = {}
    
    for year in range(start_year, end_year + 1):
        season_str = f"{year}-{str(year-2000+1).zfill(2)}"
        
        print(f"\n{'#'*60}")
        print(f"SEASON {season_str} ({year - start_year + 1}/{total_seasons})")
        print(f"{'#'*60}\n")
        
        try:
            df = get_all_shots_season(season=season_str, delay=delay, save_every=save_every)
            results[season_str] = {
                'success': True,
                'shots': len(df),
                'file': f'nba_shots_{season_str}_all.csv'
            }
        except Exception as e:
            print(f"\n✗✗ SEASON {season_str} FAILED: {str(e)}")
            results[season_str] = {
                'success': False,
                'error': str(e)
            }
        
        # Print progress summary
        elapsed = datetime.now() - overall_start
        seasons_done = year - start_year + 1
        seasons_left = total_seasons - seasons_done
        avg_per_season = elapsed / seasons_done
        est_remaining = avg_per_season * seasons_left
        
        print(f"\n{'='*60}")
        print(f"OVERALL PROGRESS: {seasons_done}/{total_seasons} seasons")
        print(f"Elapsed: {elapsed}")
        print(f"Est. remaining: {est_remaining}")
        print(f"{'='*60}\n")
    
    # Final summary
    overall_end = datetime.now()
    print(f"\n{'='*60}")
    print(f"ALL SEASONS COMPLETE!")
    print(f"Total time: {overall_end - overall_start}")
    print(f"{'='*60}\n")
    
    print("Summary:")
    total_shots = 0
    for season, info in results.items():
        if info['success']:
            print(f"  ✓ {season}: {info['shots']:,} shots → {info['file']}")
            total_shots += info['shots']
        else:
            print(f"  ✗ {season}: FAILED - {info['error']}")
    
    print(f"\nTotal shots collected: {total_shots:,}")
    
    return results


# Run the collection
if __name__ == "__main__":
    results = get_all_seasons(start_year=2000, end_year=2025, delay=0.6, save_every=5)