"""TestView class."""

# Standard Library
from http import HTTPStatus

# Django
from django.urls import reverse
from django.utils import timezone

# AA Skillfarm
from skillfarm.tests import SkillFarmTestCase
from skillfarm.tests.testdata.utils import (
    create_eve_type_price,
)
from skillfarm.views import skillfarm_calc

MODULE_PATH = "skillfarm.views"


class TestSkillFarmCalculator(SkillFarmTestCase):
    """Test Skill Calculator View."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.plex = create_eve_type_price(
            name="PLEX", eve_type_id=44992, buy=100, sell=200, updated_at=timezone.now()
        )
        cls.skillinjector = create_eve_type_price(
            name="Skill Injector",
            eve_type_id=40520,
            buy=300,
            sell=400,
            updated_at=timezone.now(),
        )
        cls.extractor = create_eve_type_price(
            name="Skill Extractor",
            eve_type_id=40519,
            buy=500,
            sell=600,
            updated_at=timezone.now(),
        )

    def test_skillcalculator_should_view_calc(self):
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
        self.assertContains(response, "PLEX")
        self.assertContains(response, "Skill Injector")
        self.assertContains(response, "Skill Extractor")

    def test_skillcalculator_should_view_calc_with_character_id(self):
        """
        Test should render skill calculator view with character id.
        """
        # given
        request = self.factory.get(reverse("skillfarm:calculator"))
        request.user = self.user
        # when
        response = skillfarm_calc(request, character_id=1001)
        # then
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertContains(response, "PLEX")
        self.assertContains(response, "Skill Injector")
        self.assertContains(response, "Skill Extractor")
