"""Forms for app."""

# Django
from django import forms

# Alliance Auth (External Libs)
from eveuniverse.models import EveType


class ConfirmForm(forms.Form):
    """Form Confirms."""

    character_id = forms.CharField(
        widget=forms.HiddenInput(),
    )


class SkillSetForm(forms.Form):
    """Form SkillSet."""

    character_id = forms.CharField(
        widget=forms.HiddenInput(),
    )

    selected_skills = forms.CharField(
        required=False,
        widget=forms.HiddenInput(),
    )

    skills = forms.ModelMultipleChoiceField(
        queryset=EveType.objects.filter(eve_group__eve_category__id=16)
        .select_related("eve_group", "eve_group__eve_category")
        .order_by("name"),
        required=False,
        widget=forms.SelectMultiple(
            attrs={
                "class": "form-select",
                "id": "skillSetSelect",
            }
        ),
    )
