"""Forms for app."""

# Third Party
from eve_sde.models.types import ItemType as EveType

# Django
from django import forms

# AA Skillfarm
from skillfarm.models.skillfarmaudit import SkillFarmSetup


class Delete(forms.Form):
    """
    Form to confirm character deletion.
    """

    class Meta:
        fields = ["character_id"]


class SwitchNotification(forms.Form):
    """
    Form to confirm switching notification for a character.
    """

    class Meta:
        fields = ["character_id"]


class SwitchMarkAsRead(forms.Form):
    """
    Form to confirm switching mark as read for a character.
    """

    class Meta:
        fields = ["character_id"]


class SkillSetForm(forms.ModelForm):
    """
    Form to edit Skillset for a character.
    """

    class Meta:
        model = SkillFarmSetup
        fields = ["skillset"]
        labels = {
            "skillset": "Skills",
        }
        querysets = {
            "skills": EveType.objects.filter(group__category__id=16)
            .select_related("group", "group__category")
            .order_by("name"),
        }

        widgets = {
            "skillset": forms.CharField(),
            "skills": forms.SelectMultiple(
                attrs={
                    "class": "form-select",
                    "id": "skillSetSelect",
                }
            ),
        }
