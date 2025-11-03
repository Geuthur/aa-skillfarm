# Standard Library
from io import StringIO
from unittest.mock import patch

# Django
from django.core.management import call_command
from django.db import IntegrityError, transaction
from django.utils import timezone

# Alliance Auth (External Libs)
from app_utils.testing import NoSocketsTestCase
from eveuniverse.models import EveType

# AA Skillfarm
from skillfarm.models.prices import EveTypePrice
from skillfarm.tests.testdata.eveuniverse import load_eveuniverse

COMMAND_PATH = "skillfarm.management.commands.skillfarm_load_prices"


@patch(COMMAND_PATH + ".requests.get")
@patch(COMMAND_PATH + ".EveType.objects.get_or_create_esi")
class TestLoadPrices(NoSocketsTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        load_eveuniverse()

        cls.json = {
            1: {"buy": {"percentile": 100}, "sell": {"percentile": 200}},
            2: {"buy": {"percentile": 300}, "sell": {"percentile": 400}},
        }

    @patch(COMMAND_PATH + ".logger")
    def test_should_load_prices(self, mock_logger, _, mock_requests_get):
        # given
        mock_requests_get.return_value.json.return_value = self.json

        # when
        call_command("skillfarm_load_prices")
        # then
        mock_logger.debug.assert_called_once_with("Created all skillfarm prices.")

    @patch("builtins.input")
    def test_load_prices_should_get_integrityerror(
        self, mock_input, _, mock_requests_get
    ):
        # given
        EveTypePrice.objects.create(
            eve_type_id=1, buy=100, sell=200, updated_at=timezone.now()
        )

        mock_input.return_value = "n"
        mock_requests_get.return_value.json.return_value = self.json

        # when
        out = StringIO()
        with transaction.atomic():
            call_command("skillfarm_load_prices", stdout=out)
        output = out.getvalue()

        # then
        self.assertIn("No changes made.", output)
        excepted_count = EveTypePrice.objects.count()
        self.assertEqual(excepted_count, 1)

    @patch("builtins.input")
    def test_load_prices_should_get_integrityerror_and_replace(
        self, mock_input, _, mock_requests_get
    ):
        # given
        EveTypePrice.objects.create(
            eve_type_id=1, buy=100, sell=200, updated_at=timezone.now()
        )
        mock_input.return_value = "y"
        mock_requests_get.return_value.json.return_value = self.json

        # when
        out = StringIO()
        call_command("skillfarm_load_prices", stdout=out)
        output = out.getvalue()

        # then
        self.assertIn("Successfully updated 2 prices.", output)
        excepted_count = EveTypePrice.objects.count()
        self.assertEqual(excepted_count, 2)

    @patch(COMMAND_PATH + ".EveType.objects.get")
    def test_load_prices_should_evetype_not_exist(
        self, mock_evetype, _, mock_requests_get
    ):
        # given
        mock_requests_get.return_value.json.return_value = {
            666: {"buy": {"percentile": 100}, "sell": {"percentile": 200}},
        }
        mock_evetype.side_effect = EveType.DoesNotExist

        # when
        out = StringIO()
        call_command("skillfarm_load_prices", stdout=out)
        output = out.getvalue()

        self.assertIn("Ensure you have loaded the data from eveuniverse.", output)
        excepted_count = EveTypePrice.objects.count()
        self.assertEqual(excepted_count, 0)

    @patch(COMMAND_PATH + ".EveType.objects")
    def test_load_prices_should_get_error(self, mock_evetype, _, mock_requests_get):
        # given
        mock_requests_get.return_value.json.return_value = {
            666: {"buy": {"percentile": 100}, "sell": {"percentile": 200}},
        }
        mock_evetype.get.return_value = EveType.objects.get(id=44992)
        mock_evetype.filter.return_value.values_list.return_value = []

        # when
        out = StringIO()
        call_command("skillfarm_load_prices", stdout=out)
        output = out.getvalue()

        self.assertIn(
            "Error: Not all required types are loaded into the database.", output
        )
        excepted_count = EveTypePrice.objects.count()
        self.assertEqual(excepted_count, 0)
