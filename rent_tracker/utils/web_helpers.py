"""Web scraping utility functions."""

import requests
import config


def check_url_exists(url: str) -> bool:
    """
    Check if a URL exists without downloading the full file.
    
    Args:
        url (str): URL to check
        
    Returns:
        bool: True if URL exists (status 200), False otherwise
    """
    headers = {'User-Agent': config.USER_AGENT}
    try:
        response = requests.head(url, headers=headers, timeout=config.REQUEST_TIMEOUT)
        return response.status_code == 200
    except:
        return False