"""Helpers for ESI tests with pook."""

# Django
from django.core.cache import cache

ESI_BASE_URL = "https://esi.evetech.net"


def skills_url(character) -> str:
    """Return the ESI URL of the skills of a SkillFarmAudit character."""
    return f"{ESI_BASE_URL}/characters/{character.character.character_id}/skills"


def skillqueue_url(character) -> str:
    """Return the ESI URL of the skillqueue of a SkillFarmAudit character."""
    return f"{ESI_BASE_URL}/characters/{character.character.character_id}/skillqueue"


def clear_esi_limits(character) -> None:
    """Remove the ESI error limit and the char-detail bucket of a character from the cache."""
    cache.delete("esi_error_limit_reset")
    cache.delete(f"esi:bucket:char-detail:{character.character.character_id}")
