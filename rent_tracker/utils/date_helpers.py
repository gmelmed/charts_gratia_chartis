"""Date utility functions."""

from datetime import date
from dateutil.relativedelta import relativedelta
from typing import List


def generate_year_month_range(end_date: date = None, years_back: int = 6) -> List[str]:
    """
    Generate a list of year-month combinations in 'yyyymm' format,
    starting from the specified end date and going back a specified number of years.

    Args:
        end_date (date, optional): The end date to start from. Defaults to today's date.
        years_back (int, optional): Number of years to go back. Defaults to 6.

    Returns:
        List[str]: List of year-month combinations in 'yyyymm' format, sorted in descending order.

    Example:
        >>> generate_year_month_range()  # If today is 2024-11-14
        ['202411', '202410', '202409', ..., '201812']
    """
    # If no end date is provided, use today's date
    if end_date is None:
        end_date = date.today()

    # Calculate start date
    start_date = end_date - relativedelta(years=years_back)

    # Initialize result list
    date_list = []

    # Current date for iteration
    current_date = end_date

    # Generate dates until we reach start date
    while current_date >= start_date:
        # Format date as 'yyyymm'
        date_str = current_date.strftime('%Y%m')
        date_list.append(date_str)
        # Move to previous month
        current_date -= relativedelta(months=1)

    return date_list