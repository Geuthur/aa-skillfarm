# Django
from django.test import TestCase
from django.utils import timezone

# Alliance Auth (External Libs)
from app_utils.testing import create_user_from_evecharacter
from eveuniverse.models import EveType

# AA Skillfarm
from skillfarm.models.skillfarm import (
    CharacterSkill,
    CharacterSkillqueueEntry,
    SkillFarmAudit,
    SkillFarmSetup,
)
from skillfarm.tests.testdata.allianceauth import load_allianceauth
from skillfarm.tests.testdata.eveuniverse import load_eveuniverse
from skillfarm.tests.testdata.skillfarm import create_skillfarm_character

MODULE_PATH = "skillfarm.models.skillfarm"


class TestSkillfarmModel(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        load_allianceauth()

        cls.audit = create_skillfarm_character(1001)

    def test_should_return_string_audit(self):
        """Test should return the Audit Character Data"""
        self.assertEqual(str(self.audit), "Gneuten's Character Data")

    def test_should_return_esi_scopes(self):
        """Test should return the ESI Scopes for Skillfarm"""
        self.assertEqual(
            self.audit.get_esi_scopes(),
            ["esi-skills.read_skills.v1", "esi-skills.read_skillqueue.v1"],
        )

    def test_is_active_should_return_false(self):
        """Test should return False for is_active Property"""
        self.assertFalse(self.audit.is_active)

    def test_is_active_should_return_true(self):
        """Test should return True for is_active Property"""
        self.audit.last_update_skills = timezone.now()
        self.audit.last_update_skillqueue = timezone.now()

        self.assertTrue(self.audit.is_active)

    def test_is_active_should_update_active_to_false(self):
        """Test should update the active field to False"""
        self.audit.active = True
        self.audit.last_update_skills = timezone.now() - timezone.timedelta(days=7)
        self.audit.last_update_skillqueue = timezone.now() - timezone.timedelta(days=7)
        self.audit.save()

        self.assertFalse(self.audit.is_active)

    def test_is_cooldown_should_return_false(self):
        """Test should return False for is_cooldown Property"""
        self.assertFalse(self.audit.is_cooldown)

    def test_is_cooldown_should_return_true(self):
        """Test should return True for is_cooldown Property"""
        self.audit.last_notification = timezone.now()
        self.assertTrue(self.audit.is_cooldown)


class TestSkillFarmHelper(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        load_allianceauth()
        load_eveuniverse()

        cls.user, cls.user_ownership = create_user_from_evecharacter(character_id=1001)

        cls.audit = SkillFarmAudit(
            name=cls.user_ownership.character.character_name,
            character=cls.user_ownership.character,
            last_update_skillqueue=timezone.now(),
            last_update_skills=timezone.now(),
        )
        cls.audit.save()

        cls.skill1 = EveType.objects.get(name="skill1")
        cls.skill2 = EveType.objects.get(name="skill2")

    def test_should_return_skill_extraction_no_skillset(self):
        """Test should return the Skill Extraction with empty list"""
        self.assertEqual(self.audit.skill_extraction(), [])

    def test_should_return_skill_extraction_skillset_without_level5(self):
        """Test should return the Skill Extraction with empty list"""
        skillfarmsetup = SkillFarmSetup.objects.create(
            character=self.audit, skillset=[self.skill1.name, self.skill2.name]
        )
        skillfarmsetup.save()

        CharacterSkill.objects.create(
            character=self.audit,
            eve_type=self.skill1,
            active_skill_level=3,
            skillpoints_in_skill=1000,
            trained_skill_level=4,
        )

        self.assertEqual(self.audit.skill_extraction(), [])

    def test_should_return_skill_extraction_skillset_with_level5(self):
        """Test should return the Skill Extraction with skill names"""
        skillfarmsetup = SkillFarmSetup.objects.create(
            character=self.audit, skillset=[self.skill1.name, self.skill2.name]
        )
        skillfarmsetup.save()

        CharacterSkill.objects.create(
            character=self.audit,
            eve_type=self.skill1,
            active_skill_level=4,
            skillpoints_in_skill=1000,
            trained_skill_level=5,
        )

        self.assertEqual(self.audit.skill_extraction(), ["skill1"])

    def test_should_return_skillqueue_extraction_empty(self):
        """Test should return the Skillqueue Extraction with empty list"""
        self.assertEqual(self.audit.skillqueue_extraction(), [])

    def test_should_return_skillqueue_extraction_skillset_with_finished_skill(self):
        """Test should return the Skillqueue Extraction with skill names"""
        skillfarmsetup = SkillFarmSetup.objects.create(
            character=self.audit, skillset=[self.skill1.name, self.skill2.name]
        )
        skillfarmsetup.save()

        CharacterSkillqueueEntry.objects.create(
            queue_position=1,
            eve_type=self.skill2,
            finished_level=5,
            start_date=timezone.now() - timezone.timedelta(days=20),
            finish_date=timezone.now() - timezone.timedelta(days=3),
            character=self.audit,
        )

        self.assertEqual(self.audit.skillqueue_extraction(), ["skill2"])

    def test_should_return_skillqueue_extraction_skillset_without_finished_skill(self):
        """Test should return the Skillqueue Extraction with skill names"""
        skillfarmsetup = SkillFarmSetup.objects.create(
            character=self.audit, skillset=[self.skill1.name, self.skill2.name]
        )
        skillfarmsetup.save()

        CharacterSkillqueueEntry.objects.create(
            queue_position=1,
            eve_type=self.skill2,
            finished_level=4,
            start_date=timezone.now() - timezone.timedelta(days=20),
            finish_date=timezone.now() - timezone.timedelta(days=3),
            character=self.audit,
        )

        self.assertEqual(self.audit.skillqueue_extraction(), [])

    def test_get_finished_skills_should_return_empty(self):
        """Test should return the finished skills with empty list"""
        self.assertEqual(self.audit.get_finished_skills(), [])

    def test_get_finished_skills_should_return_skills(self):
        """Test should return the finished skills with skill names"""
        skillfarmsetup = SkillFarmSetup.objects.create(
            character=self.audit, skillset=[self.skill1.name, self.skill2.name]
        )
        skillfarmsetup.save()

        CharacterSkill.objects.create(
            character=self.audit,
            eve_type=self.skill1,
            active_skill_level=5,
            skillpoints_in_skill=1000,
            trained_skill_level=5,
        )

        CharacterSkillqueueEntry.objects.create(
            queue_position=1,
            eve_type=self.skill2,
            finished_level=5,
            start_date=timezone.now() - timezone.timedelta(days=20),
            finish_date=timezone.now() - timezone.timedelta(days=3),
            character=self.audit,
        )

        self.assertEqual(sorted(self.audit.get_finished_skills()), ["skill1", "skill2"])
