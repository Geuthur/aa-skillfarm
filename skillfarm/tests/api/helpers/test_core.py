# Django
from django.test import RequestFactory, TestCase

# Alliance Auth (External Libs)
from app_utils.testdata_factories import UserMainFactory
from eveuniverse.models import EveType

# AA Skillfarm
from skillfarm.api.helpers import core
from skillfarm.tests.testdata.allianceauth import load_allianceauth
from skillfarm.tests.testdata.eveuniverse import load_eveuniverse
from skillfarm.tests.testdata.skillfarm import (
    create_skillfarm_character,
    create_user_from_evecharacter_with_access,
)

MODULE_PATH = "skillfarm.api.helpers."


class TestCoreHelpers(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        load_allianceauth()
        load_eveuniverse()

        cls.audit = create_skillfarm_character(1001)
        cls.factory = RequestFactory()
        cls.user, cls.character_ownership = create_user_from_evecharacter_with_access(
            1001
        )
        cls.user_2, cls.character_ownership_2 = (
            create_user_from_evecharacter_with_access(1002)
        )
        cls.no_evecharacter_user = UserMainFactory(
            permissions=[
                "skillfarm.basic_access",
            ]
        )

    def test_generate_progressbar_html(self):
        """Test the generate_progressbar_html function."""
        result = core.generate_progressbar_html(50)
        self.assertIn("width: 50.00%;", result)
        self.assertIn("50.00%", result)

    def test_get_main_character(self):
        """Test getting the main character for a user."""
        # given
        request = self.factory.get("/")
        request.user = self.user
        # when
        perm, main_character = core.get_main_character(
            request, self.character_ownership.character.character_id
        )
        # then
        self.assertEqual(
            main_character.character_id, self.character_ownership.character.character_id
        )
        self.assertTrue(perm)

    def test_get_main_character_no_permission(self):
        """Test getting a character without permission."""
        # given
        request = self.factory.get("/")
        request.user = self.no_evecharacter_user
        # when
        perm, main_character = core.get_main_character(
            request, self.character_ownership.character.character_id
        )
        # then
        self.assertFalse(perm)
        self.assertEqual(
            main_character.character_id, self.character_ownership.character.character_id
        )

    def test_get_main_character_nonexistent(self):
        """Test getting a nonexistent character."""
        # given
        request = self.factory.get("/")
        request.user = self.user_2
        # when
        perm, main_character = core.get_main_character(request, 999999999)
        # then
        self.assertTrue(perm)
        self.assertEqual(
            main_character.character_id, 1002
        )  # Is the main character of user_2
