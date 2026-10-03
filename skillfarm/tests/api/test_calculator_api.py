# Standard Library
from http import HTTPStatus

# Django
from django.urls import reverse
from django.utils import timezone

# AA Skillfarm
from skillfarm.models.prices import EveTypePrice
from skillfarm.tests import SkillFarmTestCase
from skillfarm.tests.testdata.skillfarm import EveTypePriceFactory

API_URL = "skillfarm:api"


class TestCalculatorApiEndpoints(SkillFarmTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.plex = EveTypePriceFactory(
            name="PLEX", eve_type_id=44992, buy=100, sell=200, updated_at=timezone.now()
        )
        cls.skillinjector = EveTypePriceFactory(
            name="Skill Injector",
            eve_type_id=40520,
            buy=300,
            sell=400,
            updated_at=timezone.now(),
        )
        cls.extractor = EveTypePriceFactory(
            name="Skill Extractor",
            eve_type_id=40519,
            buy=500,
            sell=600,
            updated_at=timezone.now(),
        )

    def test_get_calculator_data_should_return_profit_metrics(self):
        # Test Data
        url = reverse(f"{API_URL}:get_calculator_data")
        self.client.force_login(self.user)

        # Test Action
        response = self.client.get(url)

        # Expected Result
        self.assertEqual(response.status_code, HTTPStatus.OK)
        data = response.json()
        self.assertFalse(data["error"])
        self.assertIn("plex", data)
        self.assertIn("injector", data)
        self.assertIn("extractor", data)
        self.assertIn("month_calc", data)
        self.assertIn("month12_calc", data)
        self.assertIn("month24_calc", data)
        self.assertEqual(data["plex"]["type_id"], 44992)
        self.assertEqual(data["injector"]["type_id"], 40520)
        self.assertEqual(data["extractor"]["type_id"], 40519)

    def test_get_calculator_data_without_permission_should_return_forbidden(self):
        # Test Data
        url = reverse(f"{API_URL}:get_calculator_data")
        self.client.force_login(self.no_permission_user)

        # Test Action
        response = self.client.get(url)

        # Expected Result
        self.assertEqual(response.status_code, HTTPStatus.FORBIDDEN)

    def test_get_calculator_data_missing_prices_should_return_error_response(self):
        # Test Data
        EveTypePrice.objects.filter(eve_type_id=44992).delete()
        url = reverse(f"{API_URL}:get_calculator_data")
        self.client.force_login(self.user)

        # Test Action
        response = self.client.get(url)

        # Expected Result
        self.assertEqual(response.status_code, HTTPStatus.OK)
        data = response.json()
        self.assertTrue(data["error"])
        self.assertIn("error_message", data)
