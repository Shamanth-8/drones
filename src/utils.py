from datetime import datetime
import pandas as pd


def parse_date(date_str: str) -> datetime:
    """Parses a date string into a datetime object."""
    try:
        return pd.to_datetime(date_str)
    except Exception as e:
        print(f"Error parsing date {date_str}: {e}")
        return None


def normalize_string(s: str) -> str:
    """Normalizes a string for comparison (lowercase, stripped)."""
    if isinstance(s, str):
        return s.lower().strip()
    return ""


def calculate_duration(start_date, end_date):
    """Calculates duration in days between two dates."""
    start = parse_date(start_date)
    end = parse_date(end_date)
    if start and end:
        return (end - start).days + 1  # Inclusive
    return 0
