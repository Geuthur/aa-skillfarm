"""Django checks."""

# Django
from django.apps import apps
from django.core.checks import Warning as DjangoWarning
from django.core.checks import register


@register()
def skillfarm_config_check(app_configs, **kwargs):  # pylint: disable=W0613
    """
    skillfarm_config_check is a Django check that verifies that necessary configurations for the skillfarm app have been set up correctly in the Django settings.
    """
    warnings = []
    if not apps.is_installed(app_name="eve_sde"):
        warnings.append(
            DjangoWarning(
                "Eve SDE is not installed.",
                hint=(
                    "Eve SDE is required for the skillfarm app. "
                    "Please install it and add it to your INSTALLED_APPS."
                ),
                id="skillfarm.W001",
            )
        )
    return warnings
