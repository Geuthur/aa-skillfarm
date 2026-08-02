"""Test to ensure that the factories are working correctly."""

# AA Skillfarm
from skillfarm.tests import SkillFarmTestCase
from skillfarm.tests.testdata.factory import (
    ConstellationFactory,
    EveAllianceInfoFactory,
    EveCharacterFactory,
    EveCorporationInfoFactory,
    ItemCategoryFactory,
    ItemGroupFactory,
    ItemTypeFactory,
    RegionFactory,
    SolarSystemFactory,
)
from skillfarm.tests.testdata.skillfarm import (
    CharacterSkillFactory,
    CharacterSkillqueueEntryFactory,
    EveTypePriceFactory,
    SkillFarmAuditFactory,
    SkillFarmSetupFactory,
    UserMainFactory,
)


class TestSkillFarmFactory(SkillFarmTestCase):
    """Test the SkillFarm factories."""

    def test_can_create_user(self):
        """Test that a user can be created."""
        user = UserMainFactory()
        self.assertTrue(user.has_perm("skillfarm.basic_access"))

    def test_can_create_skill_farm_audit(self):
        """Test that a skill farm audit can be created."""
        audit = SkillFarmAuditFactory()
        self.assertTrue(audit)

    def test_can_create_skill_farm_audit_for_given_user(self):
        """Test that a skill farm audit can be created for a given user."""
        audit = SkillFarmAuditFactory(user=self.user)
        self.assertEqual(
            audit.character.character_id, self.user.profile.main_character.character_id
        )

    def test_can_create_skill_farm_setup(self):
        """Test that a skill farm setup can be created."""
        setup = SkillFarmSetupFactory()
        self.assertTrue(setup)

    def test_can_create_skill_farm_setup_for_given_user(self):
        """Test that a skill farm setup can be created for a given user."""
        audit = SkillFarmAuditFactory(user=self.user)
        setup = SkillFarmSetupFactory(character=audit)
        self.assertEqual(setup.character, audit)

    def test_can_create_character_skill(self):
        """Test that a character skill can be created."""
        skill = CharacterSkillFactory()
        self.assertTrue(skill)

    def test_can_create_character_skill_for_given_character(self):
        """Test that a character skill can be created for a given character audit."""
        audit = SkillFarmAuditFactory()
        skill = CharacterSkillFactory(character=audit)
        self.assertEqual(skill.character, audit)

    def test_can_create_character_skillqueue_entry(self):
        """Test that a character skillqueue entry can be created."""
        entry = CharacterSkillqueueEntryFactory()
        self.assertTrue(entry)

    def test_can_create_eve_type_price(self):
        """Test that an EVE type price can be created."""
        price = EveTypePriceFactory()
        self.assertTrue(price)


class TestFactory(SkillFarmTestCase):
    """Test the factories."""

    def test_can_create_eve_character(self):
        """Test that an EVE character can be created."""
        character = EveCharacterFactory()
        self.assertIsNotNone(character.character_id)

    def test_can_create_eve_corporation(self):
        """Test that an EVE corporation can be created."""
        corporation = EveCorporationInfoFactory()
        self.assertIsNotNone(corporation.corporation_id)

    def test_can_create_eve_alliance(self):
        """Test that an EVE alliance can be created."""
        alliance = EveAllianceInfoFactory()
        self.assertIsNotNone(alliance.alliance_id)

    def test_can_create_item_type(self):
        """Test that an item type can be created."""
        item_type = ItemTypeFactory()
        self.assertIsNotNone(item_type.id)

    def test_can_create_item_group(self):
        """Test that an item group can be created."""
        item_group = ItemGroupFactory()
        self.assertIsNotNone(item_group.id)

    def test_can_create_item_category(self):
        """Test that an item category can be created."""
        item_category = ItemCategoryFactory()
        self.assertIsNotNone(item_category.id)

    def test_can_create_region(self):
        """Test that a region can be created."""
        region = RegionFactory()
        self.assertIsNotNone(region.id)

    def test_can_create_constellation(self):
        """Test that a constellation can be created."""
        constellation = ConstellationFactory()
        self.assertIsNotNone(constellation.id)

    def test_can_create_solar_system(self):
        """Test that a solar system can be created."""
        solar_system = SolarSystemFactory()
        self.assertIsNotNone(solar_system.id)
