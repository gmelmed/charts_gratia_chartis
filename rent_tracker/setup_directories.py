"""Create necessary directory structure for the pipeline."""

import os

directories = [
    'data/raw',        # CHANGED: removed rent_tracker/
    'data/processed'   # CHANGED: removed rent_tracker/
]

for directory in directories:
    os.makedirs(directory, exist_ok=True)
    print(f"✓ Created directory: {directory}")

print("\n✓ Directory setup complete!")