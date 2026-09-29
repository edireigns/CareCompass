"""Explicit display policies; an old reporting period is not an expired result."""
from datetime import date, datetime

def parse_date(value):
    if not value: return None
    for fmt in ('%Y-%m-%d', '%m/%d/%Y'):
        try: return datetime.strptime(value[:10], fmt).date()
        except (ValueError, TypeError): pass
    return None

def reporting_status(end, today=None):
    day = parse_date(end)
    if day is None: return 'unknown'
    age = ((today or date.today()) - day).days
    if age < 0: return 'future_period'
    return 'older_period' if age > 730 else 'recent_period'

def directory_status(verified, expires, today=None):
    today = today or date.today()
    expiry = parse_date(expires)
    if expiry and expiry < today: return 'expired'
    checked = parse_date(verified)
    if not checked or checked > today: return 'unknown'
    return 'review_due' if (today - checked).days > 180 else 'recently_verified'
