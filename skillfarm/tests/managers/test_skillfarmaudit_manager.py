# Django
from django.test import TestCase
from django.utils import timezone

# Alliance Auth
from allianceauth.eveonline.models import EveCharacter

# AA Skillfarm
from skillfarm.models.skillfarmaudit import SkillFarmAudit
from skillfarm.tests import NoSocketsTestCase, SkillFarmTestCase
from skillfarm.tests.testdata.integrations.allianceauth import load_allianceauth
from skillfarm.tests.testdata.utils import (
    add_alt_character_to_user,
    create_character,
    create_skillfarm_character_from_user,
    create_update_status,
    create_user_from_evecharacter,
)

MODULE_PATH = "skillfarm.managers.skillfarmaudit"


class TestCharacterAnnotateTotalUpdateStatus(SkillFarmTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

    def test_should_be_ok(self):
        """
        Test should be OK when all sections are successful.
        """
        # given
        character = create_skillfarm_character_from_user(self.user)
        sections = SkillFarmAudit.UpdateSection.get_sections()
        for section in sections:
            create_update_status(
                character,
                section=section,
                is_success=True,
                error_message="",
                has_token_error=False,
                last_run_at=timezone.now(),
                last_run_finished_at=timezone.now(),
                last_update_at=timezone.now(),
                last_update_finished_at=timezone.now(),
            )

        # when/then
        self.assertEqual(character.get_status, SkillFarmAudit.UpdateStatus.OK)

        # when
        qs = SkillFarmAudit.objects.annotate_total_update_status()
        # then
        obj = qs.first()
        self.assertEqual(obj.total_update_status, SkillFarmAudit.UpdateStatus.OK)

    def test_should_be_incomplete(self):
        """
        Test should be incomplete when no sections have been updated.
        """
        # given
        character = create_skillfarm_character_from_user(self.user)
        # when/then
        self.assertEqual(character.get_status, SkillFarmAudit.UpdateStatus.INCOMPLETE)

        # when
        qs = SkillFarmAudit.objects.annotate_total_update_status()
        # then
        obj = qs.first()
        self.assertEqual(
            obj.total_update_status, SkillFarmAudit.UpdateStatus.INCOMPLETE
        )

    def test_should_be_token_error(self):
        """
        Test should be token error when any section has a token error.
        """
        # given
        character = create_skillfarm_character_from_user(self.user)
        create_update_status(
            character,
            section=character.UpdateSection.SKILLS,
            is_success=False,
            error_message="",
            has_token_error=True,
            last_run_at=timezone.now(),
            last_run_finished_at=timezone.now(),
            last_update_at=timezone.now(),
            last_update_finished_at=timezone.now(),
        )
        # when/then
        self.assertEqual(character.get_status, SkillFarmAudit.UpdateStatus.TOKEN_ERROR)
        # when
        qs = SkillFarmAudit.objects.annotate_total_update_status()
        # then
        obj = qs.first()
        self.assertEqual(
            obj.total_update_status, SkillFarmAudit.UpdateStatus.TOKEN_ERROR
        )

    def test_should_be_disabled(self):
        """
        Test should be disabled when character is inactive.
        """
        character = create_skillfarm_character_from_user(self.user, active=False)
        # given
        sections = SkillFarmAudit.UpdateSection.get_sections()
        for section in sections:
            create_update_status(
                character,
                section=section,
                is_success=True,
                error_message="",
                has_token_error=False,
                last_run_at=timezone.now(),
                last_run_finished_at=timezone.now(),
                last_update_at=timezone.now(),
                last_update_finished_at=timezone.now(),
            )

        # then
        self.assertEqual(character.get_status, SkillFarmAudit.UpdateStatus.DISABLED)
        # when
        qs = SkillFarmAudit.objects.annotate_total_update_status()
        # then
        obj = qs.first()
        self.assertEqual(obj.total_update_status, SkillFarmAudit.UpdateStatus.DISABLED)

    def test_should_be_error(self):
        """
        Test should be error when any sections have errors.
        """
        # given
        character = create_skillfarm_character_from_user(self.user)
        sections = SkillFarmAudit.UpdateSection.get_sections()
        for section in sections:
            create_update_status(
                character,
                section=section,
                is_success=False,
                error_message="",
                has_token_error=False,
                last_run_at=timezone.now(),
                last_run_finished_at=timezone.now(),
                last_update_at=timezone.now(),
                last_update_finished_at=timezone.now(),
            )

        # then
        self.assertEqual(character.get_status, SkillFarmAudit.UpdateStatus.ERROR)
        # when
        qs = SkillFarmAudit.objects.annotate_total_update_status()
        # then
        obj = qs.first()
        self.assertEqual(obj.total_update_status, SkillFarmAudit.UpdateStatus.ERROR)


class TestSkillfarmAuditVisibleTo(NoSocketsTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        load_allianceauth()
        cls.user, cls.characterownership = create_user_from_evecharacter(
            character_id=1001, permissions=["skillfarm.basic_access"]
        )

    def test_should_return_audit(self):
        # given
        character = create_skillfarm_character_from_user(self.user)
        # when
        qs = SkillFarmAudit.objects.visible_to(self.user)
        # then
        self.assertEqual(list(qs), [character])

    def test_should_return_empty_for_other_user(self):
        # given
        other_user, _ = create_user_from_evecharacter(
            character_id=1002, permissions=["skillfarm.basic_access"]
        )
        create_skillfarm_character_from_user(self.user)
        # when
        qs = SkillFarmAudit.objects.visible_to(other_user)
        # then
        self.assertEqual(list(qs), [])

    def test_should_return_multiple_audits_for_user_with_multiple_characters(self):
        # given
        character1 = create_skillfarm_character_from_user(self.user)
        alt_character = add_alt_character_to_user(user=self.user, character_id=1003)
        character2 = create_character(eve_character=alt_character.character)
        # when
        qs = SkillFarmAudit.objects.visible_to(self.user)
        # then
        self.assertCountEqual(list(qs), [character1, character2])

    def test_should_return_all_characters(self):
        # given
        other_user, _ = create_user_from_evecharacter(
            character_id=1002,
            permissions=["skillfarm.basic_access", "skillfarm.admin_access"],
        )
        character = create_skillfarm_character_from_user(self.user)
        character2 = create_skillfarm_character_from_user(other_user)
        # when
        qs = SkillFarmAudit.objects.visible_to(other_user)
        # then
        self.assertEqual(list(qs), [character, character2])


class TestSkillfarmAuditVisibleEveCharacter(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        load_allianceauth()
        cls.user, cls.characterownership = create_user_from_evecharacter(
            character_id=1001, permissions=["skillfarm.basic_access"]
        )

    def test_should_return_audit(self):
        # given
        create_skillfarm_character_from_user(self.user)
        eve_character = EveCharacter.objects.get(character_id=1001)
        # when
        qs = SkillFarmAudit.objects.visible_eve_characters(self.user)
        # then
        self.assertEqual(list(qs), [eve_character])

    def test_should_return_multiple_audits_for_user_with_multiple_characters(self):
        # given
        create_skillfarm_character_from_user(self.user)
        add_alt_character_to_user(user=self.user, character_id=1002)
        eve_character = EveCharacter.objects.get(character_id=1001)
        eve_character2 = EveCharacter.objects.get(character_id=1002)
        # when
        qs = SkillFarmAudit.objects.visible_eve_characters(self.user)
        # then
        self.assertCountEqual(list(qs), [eve_character, eve_character2])

    def test_should_return_all_characters(self):
        # given
        other_user, _ = create_user_from_evecharacter(
            character_id=1002,
            permissions=["skillfarm.basic_access", "skillfarm.admin_access"],
        )

        eve_characters = EveCharacter.objects.all()
        # when
        qs = SkillFarmAudit.objects.visible_eve_characters(other_user)
        # then
        self.assertEqual(list(qs), list(eve_characters))
