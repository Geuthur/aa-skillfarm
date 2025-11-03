# Standard Library
from datetime import datetime
from typing import Any

# Third Party
from ninja import Schema


class Message(Schema):
    message: str


class CharacterSchema(Schema):
    character_html: str | None = None
    character_id: int
    character_name: str
    corporation_id: int | None = None
    corporation_name: str | None = None
    alliance_id: int | None = None
    alliance_name: str | None = None


class SkillFarm(Schema):
    character_id: int
    character_name: str
    corporation_id: int
    corporation_name: str
    active: bool | None
    notification: bool | None
    last_update: datetime | None
    skillset: Any
    skills: Any
    skill_names: Any
    is_active: bool | None
    extraction_ready: bool | None


class SkillFarmFilter(Schema):
    characters: list[Any]
    skills: list[Any]
