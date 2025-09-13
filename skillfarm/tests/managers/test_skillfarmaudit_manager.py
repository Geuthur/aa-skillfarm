# Django
from django.test import TestCase
from django.utils import timezone

# Alliance Auth
from allianceauth.eveonline.models import EveCharacter

# AA Skillfarm
from skillfarm.models.skillfarmaudit import SkillFarmAudit
from skillfarm.tests.testdata.allianceauth import load_allianceauth
from skillfarm.tests.testdata.skillfarm import (
    add_skillfarmaudit_character_to_user,
    create_skillfarm_character,
    create_skillfarm_character_from_user,
    create_update_status,
    create_user_from_evecharacter,
    create_user_from_evecharacter_with_access,
)

MODULE_PATH = "skillfarm.managers.skillfarmaudit"


class TestCharacterAnnotateTotalUpdateStatus(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        load_allianceauth()

    def test_should_be_ok(self):
        # given
        character = create_skillfarm_character(1001)
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
        # given
        character = create_skillfarm_character(1001)
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
        # given
        character = create_skillfarm_character(1001)
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
        character = create_skillfarm_character(1001, active=False)
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
        # given
        character = create_skillfarm_character(1001)
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


class TestSkillfarmAuditVisibleTo(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        load_allianceauth()
        cls.user, cls.characterownership = create_user_from_evecharacter_with_access(
            1001
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
        other_user, _ = create_user_from_evecharacter_with_access(1002)
        create_skillfarm_character_from_user(self.user)
        # when
        qs = SkillFarmAudit.objects.visible_to(other_user)
        # then
        self.assertEqual(list(qs), [])

    def test_should_return_multiple_audits_for_user_with_multiple_characters(self):
        # given
        character1 = create_skillfarm_character_from_user(self.user)
        character2 = add_skillfarmaudit_character_to_user(self.user, 1003)
        # when
        qs = SkillFarmAudit.objects.visible_to(self.user)
        # then
        self.assertCountEqual(list(qs), [character1, character2])

    def test_should_return_all_characters(self):
        # given
        other_user, _ = create_user_from_evecharacter(
            1002, permissions=["skillfarm.basic_access", "skillfarm.admin_access"]
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
        cls.user, cls.characterownership = create_user_from_evecharacter_with_access(
            1001
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
        add_skillfarmaudit_character_to_user(self.user, 1002)
        eve_character = EveCharacter.objects.get(character_id=1001)
        eve_character2 = EveCharacter.objects.get(character_id=1002)
        # when
        qs = SkillFarmAudit.objects.visible_eve_characters(self.user)
        # then
        self.assertCountEqual(list(qs), [eve_character, eve_character2])

    def test_should_return_all_characters(self):
        # given
        other_user, _ = create_user_from_evecharacter(
            1002, permissions=["skillfarm.basic_access", "skillfarm.admin_access"]
        )

        eve_characters = EveCharacter.objects.all()
        # when
        qs = SkillFarmAudit.objects.visible_eve_characters(other_user)
        # then
        self.assertEqual(list(qs), list(eve_characters))
