from django import template
import datetime

register = template.Library()

@register.filter
def format_duration(value):
    """The format_duration filter converts raw time objects into clean, readable labels(from 2:30:00 to 2h 30m)"""
    # Check if the value is actually a timedelta object
    if not isinstance(value, datetime.timedelta):
        return value

    total_seconds = int(value.total_seconds())
    hours = total_seconds // 3600
    minutes = (total_seconds % 3600) // 60

    parts = []
    if hours > 0:
        parts.append(f"{hours}h")
    if minutes > 0:
        parts.append(f"{minutes}m")
        
    return " ".join(parts) if parts else "0m"