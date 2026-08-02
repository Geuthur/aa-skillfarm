# Third Party
import factory
import factory.fuzzy

# Django
from django.utils import timezone

# AA Skillfarm
# AA SkillFarm
from skillfarm.models import (
    CharacterSkill,
    CharacterSkillqueueEntry,
    CharacterUpdateStatus,
    EveTypePrice,
    SkillFarmAudit,
    SkillFarmSetup,
)
from skillfarm.models.helpers.update_manager import CharacterUpdateSection
from skillfarm.tests.testdata.factory import (
    BaseMetaFactory,
    EveCharacterFactory,
    ItemTypeFactory,
    UserFactory,
)
from skillfarm.tests.testdata.utils import add_character_to_user


class UserMainFactory(UserFactory):
    """Generate a User object with a main character and default permissions for SkillFarm."""

    permissions__ = ["skillfarm.basic_access"]
    scopes__ = SkillFarmAudit.get_esi_scopes()

    @factory.post_generation
    def main_character(obj, create, _, **kwargs):
        if not create:
            return
        if "character" in kwargs:
            character = kwargs["character"]
        else:
            character_name = f"{obj.first_name} {obj.last_name}"
            character = EveCharacterFactory(character_name=character_name)

        add_character_to_user(
            user=obj,
            character=character,
            is_main=True,
            scopes=obj._main_character_scopes,
        )


class SkillFarmAuditFactory(
    factory.django.DjangoModelFactory, metaclass=BaseMetaFactory[SkillFarmAudit]
):
    """
    Generate a SkillFarmAudit object.

    Args:
        user (User, optional): The user associated with the SkillFarmAudit. If not provided, it will be created.
        character (EveCharacter, optional): The character associated with the SkillFarmAudit. If not provided, it will be created.
        name (str, optional): The name of the SkillFarmAudit. If not provided, it will be derived from the character's name.
        active (bool, optional): Whether the SkillFarmAudit is active. Defaults to True.
        notification (bool, optional): Whether notifications are enabled for the SkillFarmAudit. Defaults to False.
        notification_sent (datetime, optional): The datetime when the last notification was sent. Defaults to None.
        is_read (bool, optional): Whether the SkillFarmAudit has been read. Defaults to False.
    """

    class Meta:
        model = SkillFarmAudit
        exclude = ("user",)

    user = factory.SubFactory(UserMainFactory)
    character = factory.SubFactory(
        EveCharacterFactory,
        character_id=factory.SelfAttribute(
            "..user.profile.main_character.character_id"
        ),
        character_name=factory.SelfAttribute(
            "..user.profile.main_character.character_name"
        ),
    )

    name = factory.LazyAttribute(lambda o: o.character.character_name)
    active = True
    notification = False
    notification_sent = False
    last_notification = None
    is_read = False


class SkillFarmSetupFactory(
    factory.django.DjangoModelFactory, metaclass=BaseMetaFactory[SkillFarmSetup]
):
    """Generate a SkillFarmSetup object."""

    class Meta:
        model = SkillFarmSetup
        django_get_or_create = ("character",)

    id = factory.Sequence(lambda n: n + 1)
    name = factory.LazyAttribute(lambda o: o.character.name)
    character = factory.SubFactory(SkillFarmAuditFactory)
    skillset = None


class CharacterSkillFactory(
    factory.django.DjangoModelFactory, metaclass=BaseMetaFactory[CharacterSkill]
):
    """Generate a CharacterSkill object."""

    class Meta:
        model = CharacterSkill
        django_get_or_create = ("character", "eve_type")

    character = factory.SubFactory(SkillFarmAuditFactory)
    eve_type = factory.SubFactory(ItemTypeFactory, group__category__id=16)
    skillpoints_in_skill = factory.fuzzy.FuzzyInteger(0, 5_000_000)
    trained_skill_level = factory.fuzzy.FuzzyInteger(1, 5)
    active_skill_level = factory.fuzzy.FuzzyInteger(1, 5)


class CharacterSkillqueueEntryFactory(
    factory.django.DjangoModelFactory,
    metaclass=BaseMetaFactory[CharacterSkillqueueEntry],
):
    """Generate a CharacterSkillqueueEntry object."""

    class Meta:
        model = CharacterSkillqueueEntry
        django_get_or_create = ("character", "eve_type")

    name = factory.LazyAttribute(lambda o: o.eve_type.name_en)
    character = factory.SubFactory(SkillFarmAuditFactory)
    queue_position = factory.fuzzy.FuzzyInteger(1, 20)
    finish_date = None
    finished_level = factory.fuzzy.FuzzyInteger(1, 5)
    level_end_sp = factory.fuzzy.FuzzyInteger(0, 5_000_000)
    level_start_sp = factory.fuzzy.FuzzyInteger(0, 5_000_000)
    eve_type = factory.SubFactory(ItemTypeFactory, group__category__id=16)
    start_date = None
    training_start_sp = factory.fuzzy.FuzzyInteger(0, 5_000_000)
    has_no_skillqueue = False
    last_check = None


class CharacterUpdateStatusFactory(
    factory.django.DjangoModelFactory,
    metaclass=BaseMetaFactory[CharacterUpdateStatus],
):
    """Generate a CharacterUpdateStatus object for testing."""

    class Meta:
        model = CharacterUpdateStatus
        django_get_or_create = ("character", "section")

    character = factory.SubFactory(SkillFarmAuditFactory)
    section = factory.fuzzy.FuzzyChoice(CharacterUpdateSection.values)
    is_success = factory.fuzzy.FuzzyChoice([True, False])
    error_message = factory.Faker("sentence")
    has_token_error = factory.fuzzy.FuzzyChoice([True, False])
    last_run_at = factory.fuzzy.FuzzyDateTime(
        start_dt=timezone.make_aware(timezone.datetime(2020, 1, 1)),
        end_dt=timezone.make_aware(timezone.datetime(2024, 12, 31)),
    )
    last_run_finished_at = factory.fuzzy.FuzzyDateTime(
        start_dt=timezone.make_aware(timezone.datetime(2020, 1, 1)),
        end_dt=timezone.make_aware(timezone.datetime(2024, 12, 31)),
    )
    last_update_at = factory.fuzzy.FuzzyDateTime(
        start_dt=timezone.make_aware(timezone.datetime(2020, 1, 1)),
        end_dt=timezone.make_aware(timezone.datetime(2024, 12, 31)),
    )
    last_update_finished_at = factory.fuzzy.FuzzyDateTime(
        start_dt=timezone.make_aware(timezone.datetime(2020, 1, 1)),
        end_dt=timezone.make_aware(timezone.datetime(2024, 12, 31)),
    )


class EveTypePriceFactory(
    factory.django.DjangoModelFactory, metaclass=BaseMetaFactory[EveTypePrice]
):
    """Generate an EveTypePrice object."""

    class Meta:
        model = EveTypePrice
        django_get_or_create = ("eve_type_id",)

    name = factory.Faker("word")
    eve_type_id = factory.Sequence(lambda n: n + 1)
    eve_type = factory.LazyAttribute(
        lambda obj: (
            ItemTypeFactory(
                id=obj.eve_type_id,
                name=obj.name,
                group__category__id=16,
            )
            if getattr(obj, "eve_type_id", None)
            else ItemTypeFactory(group__category__id=16)
        )
    )
    buy = factory.fuzzy.FuzzyInteger(1, 1000)
    sell = factory.fuzzy.FuzzyInteger(1, 1000)
    updated_at = factory.fuzzy.FuzzyDateTime(
        start_dt=timezone.make_aware(timezone.datetime(2020, 1, 1)),
        end_dt=timezone.make_aware(timezone.datetime(2024, 12, 31)),
    )
