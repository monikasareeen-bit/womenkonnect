# community/templatetags/time_filters.py
from django import template
from django.utils import timezone
from datetime import timedelta

register = template.Library()

@register.filter
def time_until_edit_expires(created_at):
    """
    Calculate remaining time until edit window expires (24 hours from creation)
    Returns a human-readable string like "23 hours, 45 minutes" or "30 minutes"
    """
    expiry_time = created_at + timedelta(hours=24)
    remaining = expiry_time - timezone.now()
    
    if remaining.total_seconds() <= 0:
        return None
    
    # Calculate hours and minutes
    total_seconds = int(remaining.total_seconds())
    hours = total_seconds // 3600
    minutes = (total_seconds % 3600) // 60
    
    if hours > 0:
        if minutes > 0:
            return f"{hours} hour{'s' if hours != 1 else ''}, {minutes} minute{'s' if minutes != 1 else ''}"
        return f"{hours} hour{'s' if hours != 1 else ''}"
    elif minutes > 0:
        return f"{minutes} minute{'s' if minutes != 1 else ''}"
    else:
        return "less than a minute"