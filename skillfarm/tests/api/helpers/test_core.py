# Alliance Auth
from allianceauth.eveonline.models import EveCharacter

# AA Skillfarm
from skillfarm.api.helpers import core
from skillfarm.models import SkillFarmAudit
from skillfarm.tests import SkillFarmTestCase
from skillfarm.tests.testdata.factory import EveCharacterFactory, SkillFarmAuditFactory
from skillfarm.tests.testdata.utils import add_character_to_user

MODULE_PATH = "skillfarm.api.helpers."


class TestCoreHelpers(SkillFarmTestCase):
    """Test Core Helper Functions."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.skillfarm_audit = SkillFarmAuditFactory(user=cls.user)

    def test_generate_progressbar_html(self):
        """
        Test should generate progress bar HTML correctly.
        """
        result = core.generate_progressbar_html(50)
        self.assertIn("width: 50.00%;", result)
        self.assertIn("50.00%", result)

    def test_get_main_character(self):
        """
        Test should return EveCharacter.
        """
        # given
        request = self.factory.get("/")
        request.user = self.user
        # when
        perm, main_character = core.get_auth_character_or_main(
            request, self.user_character.character_id
        )
        # then
        self.assertEqual(main_character.character_id, self.user_character.character_id)
        self.assertTrue(perm)  # Has Permission

    def test_get_main_character_no_permission(self):
        """
        Test should return EveCharacter & No Permission.
        """
        # given
        request = self.factory.get("/")
        request.user = self.user
        # when
        perm, main_character = core.get_auth_character_or_main(
            request, self.superuser_character.character_id
        )
        # then
        self.assertFalse(perm)  # No permission
        self.assertEqual(
            main_character.character_id, self.superuser_character.character_id
        )

    def test_get_main_character_nonexistent(self):
        """
        Test should return EveCharacter when character does not exist.
        """
        # given
        request = self.factory.get("/")
        request.user = self.user
        # when
        perm, main_character = core.get_auth_character_or_main(request, 999999999)
        # then
        self.assertTrue(perm)  # Has permission to own character
        self.assertEqual(
            main_character.character_id, self.user_character.character_id
        )  # Is the main character of user_2

    def test_get_skillfarm_character(self):
        """
        Test should return SkillFarmAudit.
        """
        # given
        request = self.factory.get("/")
        request.user = self.user
        # when
        perm, skillfarm_character = core.get_skillfarm_character(
            request=request, character_id=self.skillfarm_audit.character.character_id
        )
        # then
        self.assertEqual(
            skillfarm_character.character.character_id,
            self.skillfarm_audit.character.character_id,
        )
        self.assertTrue(perm)  # Has Permission

    def test_get_skillfarm_character_no_permission(self):
        """
        Test should return SkillFarmAudit & No Permission.
        """
        # given
        request = self.factory.get("/")
        request.user = self.user
        # when
        perm, skillfarm_character = core.get_skillfarm_character(
            request=request, character_id=self.superuser_character.character_id
        )
        # then
        self.assertFalse(perm)  # No permission
        self.assertIsNone(skillfarm_character)  # No SkillFarmAudit found

    def test_get_skillfarm_character_nonexistent(self):
        """
        Test should return None when SkillFarmAudit does not exist.
        """
        # given
        request = self.factory.get("/")
        request.user = self.user
        # when
        perm, skillfarm_character = core.get_skillfarm_character(
            request=request, character_id=999999999
        )
        # then
        self.assertFalse(perm)  # No permission
        self.assertIsNone(skillfarm_character)  # No SkillFarmAudit found

    def test_get_alts_queryset(self):
        """
        Test should return a queryset of alt characters linked to the main character's user.
        """
        # given
        main_char = self.user_character
        alt_character = EveCharacterFactory()
        add_character_to_user(user=self.user, character=alt_character)
        alt_chars = EveCharacter.objects.filter(id__in=[main_char.id, alt_character.id])
        # when
        alts_qs = core.get_alts_queryset(main_char)
        # then
        self.assertCountEqual(list(alt_chars), list(alts_qs))

    def test_get_alts_queryset_with_corporations(self):
        """
        Test should return a queryset of alt characters linked to the main character's user filtered by corporations.
        """
        # given
        main_char = self.user_character
        alt_character = EveCharacterFactory()
        add_character_to_user(user=self.user, character=alt_character)
        corporations = [
            alt_character.corporation.corporation_id,
            main_char.corporation.corporation_id,
        ]
        expected_chars = EveCharacter.objects.filter(
            id__in=[main_char.id, alt_character.id],
            corporation_id__in=corporations,
        )
        # when
        alts_qs = core.get_alts_queryset(main_char, corporations=corporations)
        # then
        self.assertCountEqual(list(expected_chars), list(alts_qs))
