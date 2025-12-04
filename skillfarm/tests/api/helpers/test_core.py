# AA Skillfarm
from skillfarm.api.helpers import core
from skillfarm.tests import SkillFarmTestCase
from skillfarm.tests.testdata.utils import (
    create_skillfarm_character_from_user,
)

MODULE_PATH = "skillfarm.api.helpers."


class TestCoreHelpers(SkillFarmTestCase):
    """Test Core Helper Functions."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.skillfarm_audit = create_skillfarm_character_from_user(cls.user)

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
            request, self.user_character.character.character_id
        )
        # then
        self.assertEqual(
            main_character.character_id, self.user_character.character.character_id
        )
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
            request, self.superuser_character.character.character_id
        )
        # then
        self.assertFalse(perm)  # No permission
        self.assertEqual(
            main_character.character_id, self.superuser_character.character.character_id
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
            main_character.character_id, 1001
        )  # Is the main character of user_2
