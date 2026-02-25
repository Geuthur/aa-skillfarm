"""Forms for app."""

# Django
from django import forms

# AA Skillfarm
from skillfarm.models.prices import EveType
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
            "skills": EveType.objects.filter(eve_group__eve_category__category_id=16)
            .select_related("eve_group", "eve_group__eve_category")
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
