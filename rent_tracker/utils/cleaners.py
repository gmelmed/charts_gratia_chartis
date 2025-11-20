"""Data cleaning utility functions."""


def clean_metro_name(name: str) -> str:
    """
    Clean metro area name to format: 'City, ST'
    
    Extracts first city and first state from metro area names like:
    'New York-Newark-Jersey City, NY-NJ-PA' -> 'New York, NY'
    
    Args:
        name (str): Raw metro area name
        
    Returns:
        str: Cleaned name in format 'City, ST'
    """
    parts = name.split(',')
    if len(parts) >= 2:
        city = parts[0].split('-')[0].strip()
        state = parts[1].split('-')[0].strip()
        return f"{city}, {state}"
    return name