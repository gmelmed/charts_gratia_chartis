def clean_metro_name(name: str) -> str:
    """
    clean metro area name to format: 'City, ST'
    
    extracts first city and first state from metro area names like:
    'New York-Newark-Jersey City, NY-NJ-PA' -> 'New York, NY'
    
    args:
        name (str): Raw metro area name
        
    returns:
        str: Cleaned name in format 'City, ST'
    """
    parts = name.split(',')
    if len(parts) >= 2:
        city = parts[0].split('-')[0].strip()
        state = parts[1].split('-')[0].strip()
        return f"{city}, {state}"
    return name