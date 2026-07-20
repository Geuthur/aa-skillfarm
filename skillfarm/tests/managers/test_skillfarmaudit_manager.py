# Django
from django.utils import timezone

# Alliance Auth
from allianceauth.eveonline.models import EveCharacter

# AA Skillfarm
from skillfarm.models.helpers.update_manager import CharacterUpdateSection, UpdateStatus
from skillfarm.models.skillfarmaudit import SkillFarmAudit
from skillfarm.tests import SkillFarmTestCase
from skillfarm.tests.testdata.factory import (
    CharacterUpdateStatusFactory,
    EveCharacterFactory,
    SkillFarmAuditFactory,
    UserMainFactory,
)
from skillfarm.tests.testdata.utils import (
    add_alt_character_to_user,
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
        character = SkillFarmAuditFactory(user=self.user)
        sections = CharacterUpdateSection.get_sections()
        for section in sections:
            CharacterUpdateStatusFactory(
                character=character,
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
        self.assertEqual(
            character.skillfarm_update_status.get_status(), UpdateStatus.OK
        )

    def test_should_be_incomplete(self):
        """
        Test should be incomplete when no sections have been updated.
        """
        # given
        character = SkillFarmAuditFactory(user=self.user)
        # when/then
        self.assertEqual(
            character.skillfarm_update_status.get_status(), UpdateStatus.INCOMPLETE
        )

    def test_should_be_token_error(self):
        """
        Test should be token error when any section has a token error.
        """
        # given
        character = SkillFarmAuditFactory(user=self.user)
        CharacterUpdateStatusFactory(
            character=character,
            section=CharacterUpdateSection.SKILLS,
            is_success=False,
            error_message="",
            has_token_error=True,
            last_run_at=timezone.now(),
            last_run_finished_at=timezone.now(),
            last_update_at=timezone.now(),
            last_update_finished_at=timezone.now(),
        )
        # when/then
        self.assertEqual(
            character.skillfarm_update_status.get_status(), UpdateStatus.TOKEN_ERROR
        )

    def test_should_be_disabled(self):
        """
        Test should be disabled when character is inactive.
        """
        character = SkillFarmAuditFactory(user=self.user, active=False)
        # given
        sections = CharacterUpdateSection.get_sections()
        for section in sections:
            CharacterUpdateStatusFactory(
                character=character,
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
        self.assertEqual(
            character.skillfarm_update_status.get_status(), UpdateStatus.DISABLED
        )

    def test_should_be_error(self):
        """
        Test should be error when any sections have errors.
        """
        # given
        character = SkillFarmAuditFactory(user=self.user)
        sections = CharacterUpdateSection.get_sections()
        for section in sections:
            CharacterUpdateStatusFactory(
                character=character,
                section=section,
                is_success=False,
                error_message="",
                has_token_error=False,
                last_run_at=timezone.now(),
                last_run_finished_at=timezone.now(),
                last_update_at=timezone.now(),
                last_update_finished_at=timezone.now(),
            )

        # when/then
        self.assertEqual(
            character.skillfarm_update_status.get_status(), UpdateStatus.ERROR
        )


class TestSkillfarmAuditVisibleTo(SkillFarmTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

    def test_should_return_audit(self):
        # given
        character = SkillFarmAuditFactory(user=self.user)
        # when
        qs = SkillFarmAudit.objects.visible_to(self.user)
        # then
        self.assertEqual(list(qs), [character])

    def test_should_return_empty_for_other_user(self):
        # given
        other_user = UserMainFactory()
        SkillFarmAuditFactory(user=self.user)
        # when
        qs = SkillFarmAudit.objects.visible_to(other_user)
        # then
        self.assertEqual(list(qs), [])

    def test_should_return_multiple_audits_for_user_with_multiple_characters(self):
        # given
        character1 = SkillFarmAuditFactory(user=self.user)
        # Add an alt character to the user
        eve_character = EveCharacterFactory()
        character2 = SkillFarmAuditFactory(user=self.user, character=eve_character)
        add_alt_character_to_user(
            user=self.user, character_id=character2.character.character_id
        )
        # when
        qs = SkillFarmAudit.objects.visible_to(self.user)
        # then
        self.assertCountEqual(list(qs), [character1, character2])

    def test_should_return_all_characters(self):
        # given
        other_user = UserMainFactory(
            permissions__=["skillfarm.basic_access", "skillfarm.admin_access"]
        )
        character = SkillFarmAuditFactory(user=self.user)
        character2 = SkillFarmAuditFactory(user=other_user)
        # when
        qs = SkillFarmAudit.objects.visible_to(other_user)
        # then
        self.assertEqual(list(qs), [character, character2])


class TestSkillfarmAuditVisibleEveCharacter(SkillFarmTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

    def test_should_return_audit(self):
        # given
        SkillFarmAuditFactory(user=self.user)
        eve_character = EveCharacter.objects.get(
            character_id=self.user.profile.main_character.character_id
        )
        # when
        qs = SkillFarmAudit.objects.visible_eve_characters(self.user)
        # then
        self.assertEqual(list(qs), [eve_character])

    def test_should_return_multiple_audits_for_user_with_multiple_characters(self):
        # given
        SkillFarmAuditFactory(user=self.user)
        character = EveCharacterFactory()
        add_alt_character_to_user(user=self.user, character_id=character.character_id)
        eve_character = EveCharacter.objects.get(
            character_id=self.user.profile.main_character.character_id
        )
        # when
        qs = SkillFarmAudit.objects.visible_eve_characters(self.user)
        # then
        self.assertCountEqual(list(qs), [eve_character, character])

    def test_should_return_all_characters(self):
        # given
        other_user = UserMainFactory(
            permissions__=["skillfarm.basic_access", "skillfarm.admin_access"]
        )
        eve_characters = EveCharacter.objects.all()
        # when
        qs = SkillFarmAudit.objects.visible_eve_characters(other_user)
        # then
        self.assertEqual(list(qs), list(eve_characters))
