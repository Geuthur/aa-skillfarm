"""Test to ensure that the factories are working correctly."""

# AA Skillfarm
from skillfarm.tests import SkillFarmTestCase
from skillfarm.tests.testdata.factory import (
    CharacterSkillFactory,
    CharacterSkillqueueEntryFactory,
    EveCorporationInfoFactory,
    EveTypePriceFactory,
    SkillFarmAuditFactory,
    SkillFarmSetupFactory,
    UserMainFactory,
)


class TestFactory(SkillFarmTestCase):
    """Test the factories."""

    def test_can_create_user(self):
        """Test that a user can be created."""
        user = UserMainFactory()
        self.assertTrue(user.has_perm("skillfarm.basic_access"))

    def test_can_create_skillfarm_audit(self):
        """Test that a SkillFarmAudit can be created."""
        audit = SkillFarmAuditFactory()
        self.assertTrue(audit.character.character_id)
        self.assertTrue(audit.character.character_name)

    def test_can_create_character_skill(self):
        """Test that a CharacterSkill can be created."""
        skill = CharacterSkillFactory()
        self.assertTrue(skill.character.character_id)
        self.assertTrue(skill.eve_type_id)

    def test_can_create_character_skillqueue(self):
        """Test that a CharacterSkillQueueEntry can be created."""
        skillqueue = CharacterSkillqueueEntryFactory()
        self.assertTrue(skillqueue.character.character.character_id)
        self.assertTrue(skillqueue.eve_type_id)

    def test_can_create_skillfarm_setup(self):
        """Test that a SkillFarmSetup can be created."""
        setup = SkillFarmSetupFactory()
        self.assertTrue(setup.character.character.character_id)
        self.assertTrue(setup.character.character.character_name)

    def test_can_create_eve_type_price(self):
        """Test that an EveTypePrice can be created."""
        price = EveTypePriceFactory()
        self.assertTrue(price.eve_type_id)
        self.assertTrue(price.name)

    def test_can_create_eve_corporation_info(self):
        """Test that an EveCorporationInfo can be created."""
        corp = EveCorporationInfoFactory()
        self.assertTrue(corp.corporation_id)
        self.assertTrue(corp.corporation_name)
