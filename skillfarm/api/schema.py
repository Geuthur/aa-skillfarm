from datetime import datetime
from typing import Any, List, Optional

from ninja import Schema


class Message(Schema):
    message: str


class SkillFarm(Schema):
    character_id: int
    character_name: str
    corporation_id: int
    corporation_name: str
    active: Optional[bool]
    notification: Optional[bool]
    last_update: Optional[datetime]
    skillset: Any
    skills: Any
    skill_names: Any
    is_active: Optional[bool]
    extraction_ready: Optional[bool]


class SkillFarmFilter(Schema):
    characters: List[Any]
    skills: List[Any]
