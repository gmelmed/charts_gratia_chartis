"""Main pipeline orchestrator - runs all data collection and processing scripts in order."""

import subprocess
import sys
import os
from datetime import datetime


def run_script(script_path):
    """Run a Python script and handle errors."""
    script_name = os.path.basename(script_path)
    print(f"\n{'='*70}")
    print(f"Running: {script_name}")
    print(f"{'='*70}\n")
    
    try:
        result = subprocess.run(
            [sys.executable, script_path],
            check=True,
            capture_output=False,
            text=True,
            cwd='rent_tracker'  # NEW: Set working directory to rent_tracker/
        )
        print(f"\n✓ {script_name} completed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"\n✗ {script_name} failed with error code {e.returncode}")
        return False

def main():
    """Run the complete data pipeline."""
    start_time = datetime.now()
    print(f"\n{'#'*70}")
    print(f"# RENT TRACKER DATA PIPELINE")
    print(f"# Started at: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'#'*70}")
    
    scripts = [
        'scripts/01_collect_homebuilding.py',
        'scripts/02_collect_population.py',
        'scripts/03_collect_zillow_county.py',
        'scripts/04_collect_zillow_metro.py',
        'scripts/05_merge_and_finalize.py'
    ]
    
    # Track success/failure
    results = {}
    
    for script in scripts:
        success = run_script(script)
        results[script] = success
        
        if not success:
            print(f"\n{'!'*70}")
            print(f"! Pipeline stopped due to error in {os.path.basename(script)}")
            print(f"{'!'*70}")
            break
    
    # Summary
    end_time = datetime.now()
    duration = end_time - start_time
    
    print(f"\n{'#'*70}")
    print(f"# PIPELINE SUMMARY")
    print(f"# Completed at: {end_time.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"# Duration: {duration}")
    print(f"{'#'*70}\n")
    
    for script, success in results.items():
        status = "✓ SUCCESS" if success else "✗ FAILED"
        print(f"{status}: {os.path.basename(script)}")
    
    # Exit with appropriate code
    if all(results.values()):
        print(f"\n✓ All pipeline steps completed successfully!")
        sys.exit(0)
    else:
        print(f"\n✗ Pipeline completed with errors")
        sys.exit(1)


if __name__ == "__main__":
    main()