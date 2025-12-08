"""TestView class."""

# Standard Library
from http import HTTPStatus

# Django
from django.urls import reverse

# AA Skillfarm
from skillfarm.tests import SkillFarmTestCase
from skillfarm.views import admin, character_overview, index, skillfarm_calc

MODULE_PATH = "skillfarm.views."


class TestViewAccess(SkillFarmTestCase):
    """Test General Skillfarm View Access."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

    def test_skillfarm(self):
        """
        Test should render skillfarm view with main character.
        """
        # given
        request = self.factory.get(
            reverse(
                "skillfarm:index",
                args=[self.user.profile.main_character.character_id],
            )
        )
        request.user = self.user
        # when
        response = index(
            request, character_id=self.user.profile.main_character.character_id
        )
        # then
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertContains(response, "Skillfarm")

    def test_skillfarm_no_main_character(self):
        """
        Test should render skillfarm view without character when user has no main character.
        """
        # given
        self.user.profile.main_character = None
        self.user.profile.save()
        self.user.refresh_from_db()

        request = self.factory.get(
            reverse(
                "skillfarm:index",
            )
        )
        request.user = self.user
        # when
        response = index(request)
        # then
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertContains(response, "Skillfarm")

    def test_character_overview(self):
        """
        Test should render character overview view.
        """
        # given
        request = self.factory.get(
            reverse(
                "skillfarm:character_overview",
            )
        )
        request.user = self.user
        # when
        response = character_overview(request)
        # then
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertContains(response, "Overview")

    def test_skill_calculator(self):
        """
        Test should render skill calculator view.
        """
        # given
        request = self.factory.get(reverse("skillfarm:calculator"))
        request.user = self.user
        # when
        response = skillfarm_calc(request)
        # then
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertContains(
            response, "An error occurred while fetching the market data."
        )

    def test_admin(self):
        """
        Test should render admin view for superuser.
        """
        request = self.factory.get(reverse("skillfarm:admin"))
        request.user = self.superuser
        # when
        response = admin(request)
        # then
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertContains(response, "Administration")
