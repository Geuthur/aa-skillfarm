"""Pydantic / Ninja schemas for AA Skillfarm API."""

# Standard Library
from typing import Literal

# Third Party
from ninja import Field, FilterSchema, Schema


class ActionResponse(Schema):
    """Generic action response schema."""

    success: bool
    message: str


class UserData(Schema):
    """User profile data including character identity and admin state."""

    user_id: int
    character_id: int
    character_name: str
    corporation_id: int
    corporation_name: str
    alliance_id: int | None = None
    alliance_name: str | None = None
    portrait: str | None = None
    is_admin: bool = False
    has_corp_access: bool = False


class MenuLink(Schema):
    """A single link item in the menu bar."""

    name: str
    link: str | None = None
    is_external: bool = False


class MenuSchema(Schema):
    """Top navigation menu structure."""

    left_links: list[MenuLink] = []
    right_links: list[MenuLink] = []


class CharacterFilter(FilterSchema):
    """Filter schema for skillfarm characters."""

    search: str | None = Field(
        None,
        description="Filter by character name, corporation name, or ticker",
    )
    training_status: Literal["all", "training", "paused"] = Field(
        "all",
        description="Filter by active training status",
    )
    extraction_status: Literal["all", "pending", "acknowledged", "none"] = Field(
        "all",
        description="Filter by extraction readiness and acknowledgment review state",
    )
    notification_status: Literal["all", "enabled", "disabled"] = Field(
        "all",
        description="Filter by notification enabled/disabled",
    )
    corporation_id: int | None = Field(
        None,
        description="Filter by corporation ID",
    )


class CharacterSummarySchema(Schema):
    """Summary of a skillfarm character for table and card views."""

    character_id: int
    character_name: str
    corporation_id: int
    corporation_name: str
    corporation_ticker: str
    portrait_url: str
    total_sp: int
    is_training: bool
    training_start_date: str | None = None
    training_finish_date: str | None = None
    queue_finish_date: str | None = None
    current_training_skill: str | None = None
    progress_percent: float = 0.0
    extractions_ready_count: int = 0
    extraction_acknowledged: bool = False
    extraction_acknowledged_at: str | None = None
    queue_paused_acknowledged: bool = False
    notification_enabled: bool = False
    update_status: str = "ok"  # "ok", "warning", "error", "token_error"
    last_update: str | None = None


class CharacterListResponse(Schema):
    """Response payload for character dashboard."""

    characters: list[CharacterSummarySchema]
    total_count: int
    paused_training_count: int
    pending_extractions_count: int
    acknowledged_extractions_count: int


class OverviewUserSchema(Schema):
    """Aggregated skillfarm state of a single user (grouped by main character)."""

    user_id: int
    username: str
    main_character_id: int | None = None
    main_character_name: str
    corporation_name: str = ""
    corporation_ticker: str = ""
    portrait_url: str | None = None
    character_count: int = 0
    training_count: int = 0
    paused_count: int = 0
    pending_extractions_count: int = 0


class OverviewResponse(Schema):
    """Response payload for the overview of all visible users."""

    users: list[OverviewUserSchema]


class OverviewUserCharactersResponse(CharacterListResponse):
    """Characters of a single user for the overview detail page."""

    user: OverviewUserSchema


class SkillQueueEntrySchema(Schema):
    """Schema for individual skillqueue entries."""

    skill_id: int
    skill_name: str
    finished_level: int
    finished_level_roman: str
    queue_position: int
    start_date: str | None = None
    finish_date: str | None = None
    start_sp: int = 0
    end_sp: int = 0
    training_start_sp: int = 0
    progress_percent: float = 0.0
    is_active: bool = False
    is_extractable: bool = False


class FarmedSkillSchema(Schema):
    """Schema for trained skill in character skillset."""

    skill_id: int
    skill_name: str
    active_level: int
    trained_level: int
    skillpoints: int
    is_extractable: bool = False


class CharacterDetailResponse(Schema):
    """Full detail response for a single character."""

    character: CharacterSummarySchema
    skillqueue: list[SkillQueueEntrySchema] = []
    farmed_skills: list[FarmedSkillSchema] = []
    configured_skillset: list[str] = []


class SkillSetupSchema(Schema):
    """Configured farm skillset for a character."""

    character_id: int
    character_name: str
    skillset: list[str] = []
    available_skills: list[str] = []


class SkillSetupUpdateRequest(Schema):
    """Request payload to update configured skillset."""

    selected_skills: list[str]


class CalculatorItemSchema(Schema):
    """Market price information for a trade item."""

    type_id: int
    name: str
    buy: float
    sell: float
    updated_at: str | None = None


class CalculatorResponse(Schema):
    """Skillfarm calculation and ROI summary."""

    error: bool = False
    error_message: str | None = None
    plex: CalculatorItemSchema | None = None
    injector: CalculatorItemSchema | None = None
    extractor: CalculatorItemSchema | None = None
    month_calc: float = 0.0
    month12_calc: float = 0.0
    month24_calc: float = 0.0
