# Standard Library
from typing import Any

# Third Party
from ninja import NinjaAPI, Schema

# Django
from django.core.handlers.wsgi import WSGIRequest
from django.shortcuts import get_object_or_404, render
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _

# Alliance Auth
from allianceauth.authentication.models import UserProfile
from allianceauth.services.hooks import get_extension_logger

# Alliance Auth (External Libs)
from app_utils.logging import LoggerAddTag

# AA Skillfarm
from skillfarm import __title__
from skillfarm.api.helpers.core import (
    arabic_number_to_roman,
    generate_delete_character_button,
    generate_edit_skillsetup_button,
    generate_progressbar_html,
    generate_skillinfo_button,
    generate_status_icon_html,
    generate_toggle_notification_button,
    get_alts_queryset,
    get_character,
    get_main_character,
)
from skillfarm.api.helpers.skilldetails import (
    _calculate_sum_progress_bar,
    calculate_single_progress_bar,
)
from skillfarm.api.schema import CharacterSchema
from skillfarm.helpers import lazy
from skillfarm.models.skillfarmaudit import (
    CharacterSkill,
    CharacterSkillqueueEntry,
    SkillFarmAudit,
    SkillFarmSetup,
)

logger = LoggerAddTag(get_extension_logger(__name__), __title__)


class OverviewSchema(Schema):
    portrait: str
    character: CharacterSchema
    action: str


class OverviewResponse(Schema):
    characters: list[OverviewSchema] | None = None


class SkillFarmDetailSchema(Schema):
    update_status: str
    notification: bool | None
    last_update: str | None
    is_extraction_ready: str
    is_filter: str
    progress: str | None = None


class SkillFarmDetailsSchema(Schema):
    character: CharacterSchema
    details: SkillFarmDetailSchema
    actions: str


class SkillFarmDetailsResponse(Schema):
    active_characters: list[SkillFarmDetailsSchema] | None = None
    inactive_characters: list[SkillFarmDetailsSchema] | None = None


class SkillFarmSetupSchema(Schema):
    character_id: int
    character_name: str
    skillset: list | None = None


class SkillFarmSetupResponse(Schema):
    setup: SkillFarmSetupSchema | None = None


class SkillFarmQueueSchema(Schema):
    skill: str
    start_sp: int
    end_sp: int
    trained_sp: int
    start_date: str | None = None
    finish_date: str | None = None
    progress: dict[str, Any] | None = None


class SkillFarmSkillSchema(Schema):
    skill: str
    level: int
    skillpoints: int


class SkillFarmInfoResponse(Schema):
    title: str
    character: CharacterSchema
    skillqueue: list[SkillFarmQueueSchema] | None = None
    skillqueue_filtered: list[SkillFarmQueueSchema] | None = None
    skills: list[SkillFarmSkillSchema] | None = None


def get_skillqueue_data(skill: CharacterSkillqueueEntry):
    """Get skillqueue data for a single skill"""
    level = arabic_number_to_roman(skill.finished_level)

    if skill.start_date is None:
        progress = 0
    else:
        progress = calculate_single_progress_bar(skill)

    if skill.start_date is None:
        start_date = "-"
    else:
        start_date = skill.start_date.strftime("%Y-%m-%d %H:%M")

    if skill.finish_date is None:
        end_date = "-"
    else:
        end_date = skill.finish_date.strftime("%Y-%m-%d %H:%M")

    skillqueue_response = SkillFarmQueueSchema(
        skill=f"{skill.eve_type.name} {level}",
        start_sp=skill.level_start_sp,
        end_sp=skill.level_end_sp,
        trained_sp=skill.training_start_sp,
        start_date=start_date,
        finish_date=end_date,
        progress={"html": generate_progressbar_html(progress), "value": progress},
    )
    return skillqueue_response


def get_filtered_skills_data(skill: CharacterSkill) -> list[dict[str, Any]] | None:
    """Get all Skills for the current character"""
    if skill.active_skill_level == 0:
        return None

    skills_response = SkillFarmSkillSchema(
        skill=f"{skill.eve_type.name} {arabic_number_to_roman(skill.active_skill_level)}",
        level=skill.active_skill_level,
        skillpoints=skill.skillpoints_in_skill,
    )
    return skills_response


class SkillFarmApiEndpoints:
    tags = ["SkillFarm"]

    # pylint: disable=too-many-statements, too-many-locals
    def __init__(self, api: NinjaAPI):

        @api.get(
            "/overview/", response={200: OverviewResponse, 403: dict}, tags=self.tags
        )
        def get_character_overview(
            request: WSGIRequest,
        ) -> OverviewResponse | tuple[int, dict]:
            """Get Character SkillFarm Overview"""
            logger.info(f"User {request.user} requested SkillFarm overview.")
            # Get visible characters
            chars_visible = SkillFarmAudit.objects.visible_eve_characters(request.user)

            # Check permissions
            if chars_visible is None:
                logger.warning(
                    f"User {request.user} tried to access SkillFarm overview without permissions."
                )
                return 403, {"error": "Permission Denied"}

            # Get Character IDs from visible Users
            chars_ids = chars_visible.values_list("character_id", flat=True)
            characters = UserProfile.objects.filter(
                main_character__isnull=False, main_character__character_id__in=chars_ids
            ).select_related("main_character")

            response_characters: list[OverviewSchema] = []
            for character in characters:
                try:
                    template = "skillfarm/partials/buttons/view.html"
                    button = format_html(
                        render_to_string(
                            template_name=template,
                            context={
                                "url": reverse(
                                    "skillfarm:skillfarm",
                                    kwargs={
                                        "character_id": character.main_character.character_id
                                    },
                                )
                            },
                        )
                    )

                    portrait = lazy.get_character_portrait_url(
                        character_id=character.main_character.character_id,
                        character_name=character.main_character.character_name,
                        as_html=True,
                    )

                    response_characters.append(
                        OverviewSchema(
                            portrait=portrait,
                            character=CharacterSchema(
                                character_id=character.main_character.character_id,
                                character_name=character.main_character.character_name,
                                corporation_id=character.main_character.corporation_id,
                                corporation_name=character.main_character.corporation_name,
                            ),
                            action=button,
                        )
                    )
                except AttributeError:
                    continue

            logger.info(
                f"User {request.user} successfully retrieved SkillFarm overview with {len(response_characters)} characters."
            )
            return OverviewResponse(characters=response_characters)

        @api.get(
            "{character_id}/details/",
            response={200: SkillFarmDetailsResponse, 403: dict},
            tags=self.tags,
        )
        def get_details(
            request: WSGIRequest, character_id: int
        ) -> SkillFarmDetailsResponse | tuple[int, dict]:
            """Get Character SkillFarm Details"""
            logger.info(
                f"User {request.user} requested SkillFarm details for character ID {character_id}."
            )
            # Get Main Character and check permissions
            perm, main = get_main_character(request, character_id)

            # Check permissions
            if perm is False:
                logger.warning(
                    f"User {request.user} tried to access SkillFarm details for character ID {character_id} without permissions."
                )
                return 403, {"error": "Permission Denied"}

            # Get all alts for the main character (including the main itself)
            characters = get_alts_queryset(main)
            skillfarm_characters = (
                SkillFarmAudit.objects.filter(character__in=characters)
                .select_related("character")
                .prefetch_related("skillfarm_skills", "skillfarm_skillqueue")
            )

            active_characters: list[SkillFarmDetailsSchema] = []
            inactive_characters: list[SkillFarmDetailsSchema] = []

            for character in skillfarm_characters:
                char_portrait = lazy.get_character_portrait_url(
                    character_id=character.character.character_id,
                    character_name=character.character.character_name,
                    as_html=True,
                )

                char = f"{char_portrait} {character.character.character_name} {character.get_status.bootstrap_icon()} - {character.notification_icon}"

                # Create the skillinfo button
                skill_info_html = generate_skillinfo_button(character=character)

                # Create the skillfarm action buttons
                actions = []
                actions.append(generate_toggle_notification_button(character=character))
                actions.append(generate_edit_skillsetup_button(character=character))
                actions.append(generate_delete_character_button(character=character))
                actions_html = format_html(
                    f'<div class="d-flex justify-content-end">{format_html("".join(actions))}</div>'
                )

                skillfarm_details = SkillFarmDetailsSchema(
                    character=CharacterSchema(
                        character_html=char,
                        character_id=character.character.character_id,
                        character_name=character.character.character_name,
                    ),
                    details=SkillFarmDetailSchema(
                        update_status=character.get_status,
                        notification=character.notification,
                        last_update=str(character.last_update),
                        is_extraction_ready=f"{skill_info_html} {character.extraction_icon}",
                        is_filter=generate_status_icon_html(character=character),
                    ),
                    actions=actions_html,
                )

                # Generate the progress bar for the skill queue
                if character.skillfarm_skillqueue.skill_in_training().exists() is False:
                    skillfarm_details.details.progress = str(_("No Active Training"))
                    inactive_characters.append(skillfarm_details)
                else:
                    skillqueue_response: list[SkillFarmQueueSchema] = []
                    # Get skillqueue data for each skill
                    for (
                        skill
                    ) in (
                        character.get_skillqueue
                    ):  # retrieve all skillqueue entries from character
                        skillqueue_response.append(get_skillqueue_data(skill))

                    # Calculate sum progress bar
                    skillfarm_details.details.progress = _calculate_sum_progress_bar(
                        skill_queue_response=skillqueue_response
                    )
                    active_characters.append(skillfarm_details)

            logger.info(
                f"User {request.user} successfully retrieved SkillFarm details for character ID {character_id}."
            )
            return SkillFarmDetailsResponse(
                active_characters=active_characters,
                inactive_characters=inactive_characters,
            )

        @api.get(
            "{character_id}/skillsetup/",
            response={200: SkillFarmSetupResponse, 403: dict, 404: dict},
            tags=self.tags,
        )
        def get_skillsetup(
            request, character_id: int
        ) -> SkillFarmSetupResponse | tuple[int, dict]:
            """Get Character SkillSet"""
            logger.info(
                f"User {request.user} requested SkillFarm skill setup for character ID {character_id}."
            )
            # Get Main Character and check permissions
            perm, character = get_character(request, character_id)

            if perm is False:
                logger.warning(
                    f"User {request.user} tried to access SkillFarm skill setup for character ID {character_id} without permissions."
                )
                return 403, {"error": "Permission Denied"}

            # Get SkillFarm Setup or 404
            skillfilter = get_object_or_404(SkillFarmSetup, character=character)
            skillset = skillfilter.skillset

            skillfarm_setup = SkillFarmSetupSchema(
                character_id=character.character.character_id,
                character_name=character.character.character_name,
                skillset=skillset,
            )

            logger.info(
                f"User {request.user} successfully retrieved SkillFarm skill setup for character ID {character_id}."
            )
            return SkillFarmSetupResponse(setup=skillfarm_setup)

        @api.get(
            "{character_id}/skillinfo/",
            response={200: dict, 403: str},
            tags=self.tags,
        )
        def get_skillinfo_details(request, character_id: int):
            """Get Character Skills and SkillQueue"""
            logger.info(
                f"User {request.user} requested SkillFarm skill info for character ID {character_id}."
            )
            # Get Main Character and check permissions
            perm, character = get_character(request, character_id)

            if perm is False:
                logger.warning(
                    f"User {request.user} tried to access SkillFarm skill info for character ID {character_id} without permissions."
                )
                return 403, "Permission Denied"

            response_skillqueue: list[SkillFarmQueueSchema] = []
            response_skillqueue_filtered: list[SkillFarmQueueSchema] = []
            # retrieve all skillqueue entries from character
            for skill in character.get_skillqueue:
                # Get skillqueue data for each skill
                skillqueue_response = get_skillqueue_data(skill)
                # Check if skill is filtered
                if character.is_filtered:
                    response_skillqueue_filtered.append(skillqueue_response)
                else:
                    response_skillqueue.append(skillqueue_response)

            response_skills: list[SkillFarmSkillSchema] = []
            if character.is_filtered and character.get_skillsetup is not None:
                # retrieve all skill entries from character
                for skill in character.get_skills:
                    if skill.eve_type.name in character.get_skillsetup.skillset:
                        # Get skill data for each skill
                        skill_data = get_filtered_skills_data(skill)
                        if skill_data is not None:
                            response_skills.append(skill_data)

            skillinfo_response = SkillFarmInfoResponse(
                title=str(_("Skill Info")),
                character=CharacterSchema(
                    character_id=character.character.character_id,
                    character_name=character.character.character_name,
                ),
                skillqueue=response_skillqueue,
                skillqueue_filtered=response_skillqueue_filtered,
                skills=response_skills,
            )
            logger.info(
                f"User {request.user} successfully retrieved SkillFarm skill info for character ID {character_id}."
            )
            return render(
                request,
                "skillfarm/partials/modals/view_skillqueue.html",
                context=skillinfo_response.__dict__,
            )
