"""TestView class."""

# Standard Library
from http import HTTPStatus

# Django
from django.test import RequestFactory, TestCase
from django.urls import reverse

# Alliance Auth (External Libs)
from app_utils.testdata_factories import UserMainFactory

# AA Skillfarm
from skillfarm.tests.testdata.allianceauth import load_allianceauth
from skillfarm.tests.testdata.eveuniverse import load_eveuniverse
from skillfarm.tests.testdata.skillfarm import create_user_from_evecharacter_with_access
from skillfarm.views import admin, character_overview, index, skillfarm, skillfarm_calc

MODULE_PATH = "skillfarm.views."


class TestViewAccess(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        load_allianceauth()
        load_eveuniverse()

        cls.factory = RequestFactory()
        cls.user, cls.character_ownership = create_user_from_evecharacter_with_access(
            1001
        )
        cls.no_evecharacter_user = UserMainFactory(
            permissions=[
                "skillfarm.basic_access",
            ]
        )

    def test_index(self):
        # given
        request = self.factory.get(reverse("skillfarm:index"))
        request.user = self.user
        # when
        response = index(request)
        self.assertEqual(response.status_code, HTTPStatus.FOUND)
        self.assertEqual(
            response.url,
            reverse(
                "skillfarm:skillfarm",
                args=[self.user.profile.main_character.character_id],
            ),
        )

    def test_skillfarm(self):
        # given
        request = self.factory.get(
            reverse(
                "skillfarm:skillfarm",
                args=[self.user.profile.main_character.character_id],
            )
        )
        request.user = self.user
        # when
        response = skillfarm(
            request, character_id=self.user.profile.main_character.character_id
        )
        # then
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertContains(response, "Skillfarm")

    def test_skillfarm_no_character(self):
        # given
        request = self.factory.get(
            reverse(
                "skillfarm:skillfarm",
                args=[self.user.profile.main_character.character_id],
            )
        )
        request.user = self.no_evecharacter_user
        # when
        response = skillfarm(request)
        # then
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertContains(response, "Skillfarm")

    def test_character_overview(self):
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
        # given
        request = self.factory.get(reverse("skillfarm:calc"))
        request.user = self.user
        # when
        response = skillfarm_calc(request)
        # then
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertContains(
            response, "An error occurred while fetching the market data."
        )

    def test_admin(self):
        # given
        self.user.is_superuser = True
        self.user.save()

        request = self.factory.get(reverse("skillfarm:admin"))
        request.user = self.user
        # when
        response = admin(request)
        # then
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertContains(response, "Administration")
