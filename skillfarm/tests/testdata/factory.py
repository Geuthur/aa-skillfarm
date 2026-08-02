"""
Factory for Alliance Auth and Django EVE SDE.

This module provides factory classes for generating test data for Alliance Auth and Django EVE SDE.
"""

# Standard Library
from typing import Generic, TypeVar

# Third Party
import factory
import factory.fuzzy

# Django
from django.contrib.auth import get_user_model
from django.db.models import Max

# Alliance Auth
from allianceauth.eveonline.models import (
    EveAllianceInfo,
    EveCharacter,
    EveCorporationInfo,
)
from allianceauth.tests.auth_utils import AuthUtils

# Alliance Auth (External Libs)
from eve_sde.models import (
    Constellation,
    ItemCategory,
    ItemGroup,
    ItemType,
    Planet,
    Region,
    SolarSystem,
)

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

    @factory.post_generation
    def scopes(obj, create, extracted, **kwargs):
        """Set default scopes. Overwrite with `scopes=["scope1"]`."""
        if not create:
            return
        scopes = extracted or []
        obj._main_character_scopes = scopes

    @classmethod
    def _after_postgeneration(cls, obj, create, results=None):
        """Reset permission cache to force an update."""
        super()._after_postgeneration(obj, create, results)
        if hasattr(obj, "_perm_cache"):
            del obj._perm_cache
        if hasattr(obj, "_user_perm_cache"):
            del obj._user_perm_cache


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


class ItemCategoryFactory(
    factory.django.DjangoModelFactory, metaclass=BaseMetaFactory[ItemCategory]
):
    """Generate an ItemCategory object for testing."""

    class Meta:
        model = ItemCategory
        django_get_or_create = ("id",)

    id = factory.Sequence(lambda n: n + 1)
    name = factory.Faker("word")
    published = True
    icon_id = factory.fuzzy.FuzzyInteger(0, 100)


class ItemGroupFactory(
    factory.django.DjangoModelFactory, metaclass=BaseMetaFactory[ItemGroup]
):
    """Generate an ItemGroup object for testing."""

    class Meta:
        model = ItemGroup
        django_get_or_create = ("id",)

    id = factory.Sequence(lambda n: n + 1)
    name = factory.Faker("word")
    anchorable = False
    anchored = False
    category = factory.SubFactory(ItemCategoryFactory)
    fittable_non_singleton = False
    icon_id = factory.fuzzy.FuzzyInteger(0, 100)
    published = True
    use_base_price = False


class ItemTypeFactory(
    factory.django.DjangoModelFactory, metaclass=BaseMetaFactory[ItemType]
):
    """Generate an ItemType object for testing."""

    class Meta:
        model = ItemType
        django_get_or_create = ("id",)

    id = factory.Sequence(lambda n: n + 1)
    name = factory.Faker("word")
    base_price = factory.fuzzy.FuzzyFloat(1, 10000, 2)
    capacity = factory.fuzzy.FuzzyFloat(0, 1000, 2)
    description = factory.Faker("sentence")
    faction_id_raw = factory.fuzzy.FuzzyInteger(0, 100)
    graphic_id = factory.fuzzy.FuzzyInteger(0, 100)
    group = factory.SubFactory(ItemGroupFactory)
    icon_id = factory.fuzzy.FuzzyInteger(0, 100)
    market_group = None  # This can be set to a MarketGroup object if needed
    mass = factory.fuzzy.FuzzyDecimal(0, 1000, 2)
    meta_group_id_raw = factory.fuzzy.FuzzyInteger(0, 10)
    portion_size = factory.fuzzy.FuzzyInteger(0, 1000)
    published = True
    race_id = factory.fuzzy.FuzzyInteger(0, 10)
    radius = factory.fuzzy.FuzzyFloat(0, 1000, 2)
    sound_id = None  # Not needed for testing, can be set to a Sound object if needed
    variation_parent_type_id = factory.fuzzy.FuzzyInteger(0, 1000)
    volume = factory.fuzzy.FuzzyFloat(0, 1000, 2)
    packaged_volume = factory.fuzzy.FuzzyFloat(0, 1000, 2)


class RegionFactory(
    factory.django.DjangoModelFactory, metaclass=BaseMetaFactory[Region]
):
    """Generate a Region object for testing."""

    class Meta:
        model = Region
        django_get_or_create = ("id",)

    id = factory.Sequence(lambda n: n + 1)
    name = factory.Faker("word")
    x = factory.fuzzy.FuzzyFloat(-1000, 1000, 2)
    y = factory.fuzzy.FuzzyFloat(-1000, 1000, 2)
    z = factory.fuzzy.FuzzyFloat(-1000, 1000, 2)

    description = factory.Faker("sentence")
    faction_id_raw = factory.fuzzy.FuzzyInteger(0, 100)
    nebular_id_raw = factory.fuzzy.FuzzyInteger(0, 100)
    wormhole_class_id_raw = factory.fuzzy.FuzzyInteger(0, 10)


class ConstellationFactory(
    factory.django.DjangoModelFactory, metaclass=BaseMetaFactory[Constellation]
):
    """Generate a Constellation object for testing."""

    class Meta:
        model = Constellation
        django_get_or_create = ("id",)

    id = factory.Sequence(lambda n: n + 1)
    name = factory.Faker("word")
    x = factory.fuzzy.FuzzyFloat(-1000, 1000, 2)
    y = factory.fuzzy.FuzzyFloat(-1000, 1000, 2)
    z = factory.fuzzy.FuzzyFloat(-1000, 1000, 2)

    region = factory.SubFactory(RegionFactory)
    faction_id_raw = factory.fuzzy.FuzzyInteger(0, 100)
    wormhole_class_id_raw = factory.fuzzy.FuzzyInteger(0, 10)


class SolarSystemFactory(
    factory.django.DjangoModelFactory, metaclass=BaseMetaFactory[SolarSystem]
):
    """Generate a SolarSystem object for testing."""

    class Meta:
        model = SolarSystem
        django_get_or_create = ("id",)

    id = factory.Sequence(lambda n: n + 1)
    name = factory.Faker("word")
    x = factory.fuzzy.FuzzyFloat(-1000, 1000, 2)
    y = factory.fuzzy.FuzzyFloat(-1000, 1000, 2)
    z = factory.fuzzy.FuzzyFloat(-1000, 1000, 2)

    border = False
    constellation = factory.SubFactory(ConstellationFactory)
    corridor = False
    faction_id_raw = factory.fuzzy.FuzzyInteger(0, 100)
    fringe = False
    hub = False
    international = False
    luminosity = factory.fuzzy.FuzzyFloat(0, 1000, 2)
    radius = factory.fuzzy.FuzzyFloat(0, 1000, 2)
    regional = False
    security_class = factory.fuzzy.FuzzyChoice([None, "A", "B", "C", "D", "E"])
    security_status = factory.fuzzy.FuzzyFloat(0, 1, 2)
    star_id_raw = factory.fuzzy.FuzzyInteger(0, 100)
    visual_effect = factory.fuzzy.FuzzyText(length=20)
    wormhole_class_id_raw = factory.fuzzy.FuzzyInteger(0, 10)
    security_status = factory.fuzzy.FuzzyFloat(0, 1, 2)

    x_2d = factory.fuzzy.FuzzyFloat(-1000, 1000, 2)
    y_2d = factory.fuzzy.FuzzyFloat(-1000, 1000, 2)


class PlanetFactory(
    factory.django.DjangoModelFactory, metaclass=BaseMetaFactory[Planet]
):
    """Generate a Planet object for testing."""

    class Meta:
        model = Planet
        django_get_or_create = ("id",)

    id = factory.Sequence(lambda n: n + 1)
    name = factory.Faker("word")

    x = factory.fuzzy.FuzzyFloat(-1000, 1000, 2)
    y = factory.fuzzy.FuzzyFloat(-1000, 1000, 2)
    z = factory.fuzzy.FuzzyFloat(-1000, 1000, 2)

    celestial_index = factory.fuzzy.FuzzyInteger(1, 100)
    item_type = factory.SubFactory(ItemTypeFactory)
    orbit_id_raw = factory.fuzzy.FuzzyInteger(1, 100)
    orbit_index = factory.fuzzy.FuzzyInteger(1, 100)
    radius = factory.fuzzy.FuzzyFloat(1, 1000, 2)
    solar_system = factory.SubFactory(SolarSystemFactory)
