"""
App Settings
"""

# Django
from django.conf import settings

# Set Naming on Auth Hook
SKILLFARM_APP_NAME = getattr(settings, "SKILLFARM_APP_NAME", "Skillfarm")

# If True you need to set up the Logger
SKILLFARM_LOGGER_USE = getattr(settings, "SKILLFARM_LOGGER_USE", False)

# Max Time to set Char Inactive
SKILLFARM_CHAR_MAX_INACTIVE_DAYS = getattr(
    settings, "SKILLFARM_CHAR_MAX_INACTIVE_DAYS", 3
)

# Batch Size for Bulk Methods
SKILLFARM_BULK_METHODS_BATCH_SIZE = getattr(
    settings, "SKILLFARM_BULK_METHODS_BATCH_SIZE", 500
)

# Set Notification Cooldown in Days
SKILLFARM_NOTIFICATION_COOLDOWN = getattr(
    settings, "SKILLFARM_NOTIFICATION_COOLDOWN", 3
)
# Global timeout for tasks in seconds to reduce task accumulation during outages.
SKILLFARM_TASKS_TIME_LIMIT = getattr(settings, "SKILLFARM_TASKS_TIME_LIMIT", 7200)

# Price Source default is Jita
SKILLFARM_PRICE_SOURCE_ID = getattr(settings, "SKILLFARM_PRICE_SOURCE_ID", 60003760)

SKILLFARM_STALE_TYPES = {
    "skills": 30,
    "skillqueue": 30,
}
