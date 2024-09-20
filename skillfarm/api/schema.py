from datetime import datetime
from typing import Any, List, Optional

from ninja import Schema


class Message(Schema):
    message: str


class Character(Schema):
    character_name: str
    character_id: int
    corporation_id: int
    corporation_name: str
    alliance_id: Optional[int] = None
    alliance_name: Optional[str] = None


class EveName(Schema):
    id: int
    name: str
    cat: Optional[str] = None


class CharacterAdmin(Schema):
    character: Optional[dict] = None


class SkillFarm(Schema):
    character_id: int
    character_name: str
    corporation_id: int
    corporation_name: str
    active: Optional[bool]
    notification: Optional[bool]
    last_update: Optional[datetime]
    skills: Any


class SkillFarmFilter(Schema):
    characters: List[Any]
    skills: List[Any]
