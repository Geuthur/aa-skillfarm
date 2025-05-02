"""TestView class."""

# Standard Library
from http import HTTPStatus
from unittest.mock import Mock, patch

# Django
from django.test import RequestFactory, TestCase
from django.urls import reverse
from django.utils import timezone

# AA Skillfarm
from skillfarm.tests.testdata.allianceauth import load_allianceauth
from skillfarm.tests.testdata.eveuniverse import load_eveuniverse
from skillfarm.tests.testdata.skillfarm import (
    create_evetypeprice,
    create_skillfarm_character,
    create_user_from_evecharacter_with_access,
)
from skillfarm.views import skillfarm_calc

MODULE_PATH = "skillfarm.views"


class TestSkillFarmCalculator(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        load_allianceauth()
        load_eveuniverse()

        cls.factory = RequestFactory()
        cls.user, _ = create_user_from_evecharacter_with_access(1001)

        cls.plex = create_evetypeprice(
            44992, buy=100, sell=200, updated_at=timezone.now()
        )
        cls.skillinjector = create_evetypeprice(
            40520, buy=300, sell=400, updated_at=timezone.now()
        )
        cls.extractor = create_evetypeprice(
            40519, buy=500, sell=600, updated_at=timezone.now()
        )

    def test_skillcalculator_should_view_calc(self):
        # given
        request = self.factory.get(reverse("skillfarm:calc"))
        request.user = self.user
        # when
        response = skillfarm_calc(request)
        # then
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertContains(response, "PLEX")
        self.assertContains(response, "Skill Injector")
        self.assertContains(response, "Skill Extractor")

    def test_skillcalculator_should_view_calc_with_character_id(self):
        # given
        request = self.factory.get(reverse("skillfarm:calc"))
        request.user = self.user
        # when
        response = skillfarm_calc(request, character_id=1001)
        # then
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertContains(response, "PLEX")
        self.assertContains(response, "Skill Injector")
        self.assertContains(response, "Skill Extractor")
