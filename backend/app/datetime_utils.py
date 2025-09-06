"""
Utility functions for safe datetime operations
"""
from datetime import datetime, timezone
from typing import Optional

def safe_datetime_comparison(
    dt1: Optional[datetime], 
    dt2: Optional[datetime] = None
) -> tuple[Optional[datetime], Optional[datetime]]:
    """
    Safely compare two datetime objects by ensuring they have consistent timezone info.
    
    Args:
        dt1: First datetime (usually from database)
        dt2: Second datetime (usually current time, defaults to now(timezone.utc))
        
    Returns:
        Tuple of (dt1, dt2) with consistent timezone info
    """
    if dt2 is None:
        dt2 = datetime.now(timezone.utc)
    
    if dt1 is None:
        return None, dt2
    
    # If dt1 is naive (no timezone), assume it's UTC and make it timezone-aware
    if dt1.tzinfo is None:
        dt1 = dt1.replace(tzinfo=timezone.utc)
    
    # If dt2 is naive (no timezone), assume it's UTC and make it timezone-aware
    if dt2.tzinfo is None:
        dt2 = dt2.replace(tzinfo=timezone.utc)
    
    return dt1, dt2

def is_datetime_expired(
    expires_at: Optional[datetime], 
    current_time: Optional[datetime] = None
) -> bool:
    """
    Safely check if a datetime has expired.
    
    Args:
        expires_at: The expiration datetime (from database)
        current_time: Current time to compare against (defaults to now(timezone.utc))
        
    Returns:
        True if expired, False if not expired or expires_at is None
    """
    if expires_at is None:
        return False
    
    expires_at, current_time = safe_datetime_comparison(expires_at, current_time)
    
    if expires_at is None or current_time is None:
        return False
    
    return expires_at < current_time

def safe_current_time() -> datetime:
    """
    Get current time in UTC timezone.
    """
    return datetime.now(timezone.utc)

def make_timezone_aware(dt: Optional[datetime]) -> Optional[datetime]:
    """
    Make a datetime timezone-aware if it's naive (assumes UTC).
    
    Args:
        dt: DateTime to convert
        
    Returns:
        Timezone-aware datetime or None if input was None
    """
    if dt is None:
        return None
    
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    
    return dt
