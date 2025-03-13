from django.contrib import admin
from django.utils.html import format_html

from allianceauth.eveonline.evelinks import eveimageserver

from skillfarm.models.skillfarm import SkillFarmAudit


# TODO make a ETAG Cache clear option?
@admin.register(SkillFarmAudit)
class SkillFarmAuditAdmin(admin.ModelAdmin):
    """Admin Interface for Characters"""

    model = SkillFarmAudit
    model._meta.verbose_name = "Character"
    model._meta.verbose_name_plural = "Characters"

    list_display = (
        "_entity_pic",
        "_character__character_id",
        "_character__character_name",
        "_last_update_skillqueue",
        "_last_update_skills",
    )

    list_display_links = (
        "_entity_pic",
        "_character__character_id",
        "_character__character_name",
    )

    list_select_related = ("character",)

    ordering = ["character__character_name"]

    search_fields = ["character__character_name", "character__character_id"]

    actions = [
        "delete_objects",
    ]

    @admin.display(description="")
    def _entity_pic(self, obj: SkillFarmAudit):
        eve_id = obj.character.character_id
        return format_html(
            '<img src="{}" class="img-circle">',
            eveimageserver._eve_entity_image_url("character", eve_id, 32),
        )

    @admin.display(description="Character ID", ordering="character__character_id")
    def _character__character_id(self, obj: SkillFarmAudit):
        return obj.character.character_id

    @admin.display(description="Character Name", ordering="character__character_name")
    def _character__character_name(self, obj: SkillFarmAudit):
        return obj.character.character_name

    @admin.display(
        description="Last Update Skillqueue", ordering="last_update_skillqueue"
    )
    def _last_update_skillqueue(self, obj: SkillFarmAudit):
        return obj.last_update_skillqueue

    @admin.display(description="Last Update Skills", ordering="last_update_skills")
    def _last_update_skills(self, obj: SkillFarmAudit):
        return obj.last_update_skills

    # pylint: disable=unused-argument
    def has_add_permission(self, request):
        return False

    # pylint: disable=unused-argument
    def has_change_permission(self, request, obj=None):
        return False
