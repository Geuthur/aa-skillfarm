"""Time helpers."""

# Django
from django.utils import timezone


def str_normalize_time(evetime, hours: bool = False) -> str:
    """Normalize eve time to a string."""
    if hours:
        return timezone.localtime(evetime).strftime("%Y-%m-%d %H:%M")
    return timezone.localtime(evetime).strftime("%Y-%m-%d")
