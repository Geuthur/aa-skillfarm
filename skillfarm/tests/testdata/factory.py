# Standard Library
from typing import Generic, TypeVar

# Third Party
import factory
import factory.fuzzy

# Django
from django.contrib.auth import get_user_model
from django.db.models import Max
from django.utils import timezone

# Alliance Auth
from allianceauth.eveonline.models import (
    EveAllianceInfo,
    EveCharacter,
    EveCorporationInfo,
)
from allianceauth.tests.auth_utils import AuthUtils

# Alliance Auth (External Libs)
from eve_sde.models import ItemType

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
from skillfarm.tests.testdata.utils import add_character_to_user

T = TypeVar("T")
User = get_user_model()


class BaseMetaFactory(Generic[T], factory.base.FactoryMetaClass):
    def __call__(cls, *args, **kwargs) -> T:
        return super().__call__(*args, **kwargs)


class UserFactory(factory.django.DjangoModelFactory, metaclass=BaseMetaFactory[User]):
    """Generate a User object."""

    class Meta:
        model = User
        django_get_or_create = ("username",)
        exclude = ("_generated_name",)

    _generated_name = factory.Faker("name")
    username = factory.LazyAttribute(lambda obj: obj._generated_name.replace(" ", "_"))
    first_name = factory.LazyAttribute(lambda obj: obj._generated_name.split(" ")[0])
    last_name = factory.LazyAttribute(lambda obj: obj._generated_name.split(" ")[1])
    email = factory.LazyAttribute(
        lambda obj: f"{obj.first_name.lower()}.{obj.last_name.lower()}@example.com"
    )

    @factory.post_generation
    def permissions(obj, create, extracted, **kwargs):
        """Set default permissions. Overwrite with `permissions=["app.perm1"]`."""
        if not create:
            return
        permissions = extracted or []
        for permission_name in permissions:
            AuthUtils.add_permission_to_user_by_name(permission_name, obj)

    @classmethod
    def _after_postgeneration(cls, obj, create, results=None):
        """Reset permission cache to force an update."""
        super()._after_postgeneration(obj, create, results)
        if hasattr(obj, "_perm_cache"):
            del obj._perm_cache
        if hasattr(obj, "_user_perm_cache"):
            del obj._user_perm_cache


class UserMainFactory(UserFactory):
    """Generate a User object with a main character and default permissions for SkillFarm."""

    permissions__ = ["skillfarm.basic_access"]

    @factory.post_generation
    def main_character(obj, create, _, **kwargs):
        if not create:
            return
        if "character" in kwargs:
            character = kwargs["character"]
        else:
            character_name = f"{obj.first_name} {obj.last_name}"
            character = EveCharacterFactory(character_name=character_name)

        scopes = kwargs.get("scopes", SkillFarmAudit.get_esi_scopes())
        add_character_to_user(
            user=obj, character=character, is_main=True, scopes=scopes
        )


class EveAllianceInfoFactory(
    factory.django.DjangoModelFactory, metaclass=BaseMetaFactory[EveAllianceInfo]
):
    """Generate an EveAllianceInfo object."""

    class Meta:
        model = EveAllianceInfo
        django_get_or_create = ("alliance_id", "alliance_name")

    alliance_name = factory.Faker("catch_phrase")
    alliance_ticker = factory.LazyAttribute(lambda obj: obj.alliance_name[:4].upper())
    executor_corp_id = 0

    @factory.lazy_attribute
    def alliance_id(self):
        last_id = (
            EveAllianceInfo.objects.aggregate(Max("alliance_id"))["alliance_id__max"]
            or 99_000_000
        )
        return last_id + 1


class EveCorporationInfoFactory(
    factory.django.DjangoModelFactory, metaclass=BaseMetaFactory[EveCorporationInfo]
):
    """Generate an EveCorporationInfo object."""

    class Meta:
        model = EveCorporationInfo
        django_get_or_create = ("corporation_id", "corporation_name")

    corporation_name = factory.Faker("catch_phrase")
    corporation_ticker = factory.LazyAttribute(
        lambda obj: obj.corporation_name[:4].upper()
    )
    member_count = factory.fuzzy.FuzzyInteger(1000)

    @factory.lazy_attribute
    def corporation_id(self):
        last_id = (
            EveCorporationInfo.objects.aggregate(Max("corporation_id"))[
                "corporation_id__max"
            ]
            or 98_000_000
        )
        return last_id + 1

    @factory.post_generation
    def create_alliance(obj, create, extracted, **kwargs):
        if not create or extracted is False or obj.alliance:
            return
        obj.alliance = EveAllianceInfoFactory(executor_corp_id=obj.corporation_id)


class EveCharacterFactory(
    factory.django.DjangoModelFactory, metaclass=BaseMetaFactory[EveCharacter]
):
    """
    Generate an EveCharacter object.

    Args:
        character_name (str): The name of the EveCharacter.
        corporation (EveCorporationInfo, optional): The EveCorporationInfo object associated with the character. If not provided, it will be created.
        corporation_id (int): The ID of the corporation associated with the character.
        corporation_name (str): The name of the corporation associated with the character.
        corporation_ticker (str): The ticker of the corporation associated with the character.
        character_id (int): The unique ID for the character. If not provided, it will be generated.
        alliance_id (int): The ID of the alliance associated with the character's corporation. If not provided, it will be derived from the corporation.
        alliance_name (str): The name of the alliance associated with the character's corporation. If not provided, it will be derived from the corporation.
        alliance_ticker (str): The ticker of the alliance associated with the character's corporation. If not provided, it will be derived from the corporation.
    """

    class Meta:
        model = EveCharacter
        django_get_or_create = ("character_id", "character_name")
        exclude = ("corporation",)

    character_name = factory.Faker("name")
    corporation = factory.SubFactory(EveCorporationInfoFactory)
    corporation_id = factory.LazyAttribute(lambda obj: obj.corporation.corporation_id)
    corporation_name = factory.LazyAttribute(
        lambda obj: obj.corporation.corporation_name
    )
    corporation_ticker = factory.LazyAttribute(
        lambda obj: obj.corporation.corporation_ticker
    )

    @factory.lazy_attribute
    def character_id(self):
        last_id = (
            EveCharacter.objects.aggregate(Max("character_id"))["character_id__max"]
            or 90_000_000
        )
        return last_id + 1

    @factory.lazy_attribute
    def alliance_id(self):
        return (
            self.corporation.alliance.alliance_id if self.corporation.alliance else None
        )

    @factory.lazy_attribute
    def alliance_name(self):
        return (
            self.corporation.alliance.alliance_name if self.corporation.alliance else ""
        )

    @factory.lazy_attribute
    def alliance_ticker(self):
        return (
            self.corporation.alliance.alliance_ticker
            if self.corporation.alliance
            else ""
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
    eve_type = factory.LazyFunction(
        lambda: ItemType.objects.filter(group__category__id=16).order_by("?").first()
    )
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
    eve_type = factory.LazyFunction(
        lambda: ItemType.objects.filter(group__category__id=16).order_by("?").first()
    )
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
            ItemType.objects.get_or_create(
                id=obj.eve_type_id,
                defaults={"name": obj.name, "group_id": 3},
            )[0]
            if getattr(obj, "eve_type_id", None)
            else ItemType.objects.filter(group__category__id=16).order_by("?").first()
        )
    )
    buy = factory.fuzzy.FuzzyInteger(1, 1000)
    sell = factory.fuzzy.FuzzyInteger(1, 1000)
    updated_at = factory.fuzzy.FuzzyDateTime(
        start_dt=timezone.make_aware(timezone.datetime(2020, 1, 1)),
        end_dt=timezone.make_aware(timezone.datetime(2024, 12, 31)),
    )
