"""Tests for the providers module."""

# Standard Library
from unittest.mock import MagicMock, patch

# Django
from django.test import override_settings

# Alliance Auth
from esi.exceptions import (
    ESIBucketLimitException,
    ESIErrorLimitException,
    HTTPClientError,
    HTTPServerError,
)

# Alliance Auth (External Libs)
from eve_sde.models.types import ItemGroup, ItemType

# AA Skillfarm
from skillfarm.providers import esi, retry_task_on_esi_error
from skillfarm.tests import NoSocketsTestCase


@override_settings(CELERY_ALWAYS_EAGER=True, CELERY_EAGER_PROPAGATES_EXCEPTIONS=True)
class TestRetryTaskOnESIError(NoSocketsTestCase):
    """Tests for retry_task_on_esi_error context manager."""

    def setUp(self):
        """
        Set up test case with a mock Celery task.
        """
        super().setUp()
        self.task = MagicMock()
        self.task.request.retries = 1
        self.task.retry = MagicMock(side_effect=Exception("Retry called"))

    @patch("skillfarm.providers.random.uniform")
    def test_should_retry_on_esi_error_limit_exception(self, mock_random):
        """
        Test should retry task when ESI error limit is reached.
        """
        # given
        mock_random.return_value = 3.0  # Fixed jitter for testing
        reset_time = 60.0
        exc = ESIErrorLimitException(reset_time)

        # when/then
        with self.assertRaises(Exception) as context:
            with retry_task_on_esi_error(self.task):
                raise exc

        # Verify retry was called with correct countdown
        self.assertEqual(str(context.exception), "Retry called")
        self.task.retry.assert_called_once()
        call_kwargs = self.task.retry.call_args[1]
        self.assertEqual(call_kwargs["exc"], exc)
        self.assertEqual(call_kwargs["countdown"], 63)

    @patch("skillfarm.providers.random.uniform")
    def test_should_retry_on_esi_bucket_limit_exception(self, mock_random):
        """
        Test should retry task when ESI bucket limit is reached.
        """
        # given
        mock_random.return_value = 4.0  # Fixed jitter for testing
        reset_time = 30.0
        bucket_name = "test_bucket"
        exc = ESIBucketLimitException(bucket=bucket_name, reset=reset_time)

        # when/then
        with self.assertRaises(Exception) as context:
            with retry_task_on_esi_error(self.task):
                raise exc

        # Verify retry was called with correct countdown
        self.assertEqual(str(context.exception), "Retry called")
        self.task.retry.assert_called_once()
        call_kwargs = self.task.retry.call_args[1]
        self.assertEqual(call_kwargs["exc"], exc)
        self.assertEqual(call_kwargs["countdown"], 34)

    @patch("skillfarm.providers.random.uniform")
    def test_should_retry_on_http_502_error(self, mock_random):
        """
        Test should retry task on HTTP 502 Bad Gateway error.
        """
        # given
        mock_random.return_value = 2.5  # Fixed jitter for testing
        exc = HTTPServerError(502, {}, b"Bad Gateway")

        # when/then
        with self.assertRaises(Exception) as context:
            with retry_task_on_esi_error(self.task):
                raise exc

        # Verify retry was called with 60 second countdown + jitter
        self.assertEqual(str(context.exception), "Retry called")
        self.task.retry.assert_called_once()
        call_kwargs = self.task.retry.call_args[1]
        self.assertEqual(call_kwargs["exc"], exc)
        self.assertEqual(call_kwargs["countdown"], 62)

    @patch("skillfarm.providers.random.uniform")
    def test_should_retry_on_http_503_error(self, mock_random):
        """
        Test should retry task on HTTP 503 Service Unavailable error.
        """
        # given
        mock_random.return_value = 3.5  # Fixed jitter for testing
        exc = HTTPServerError(503, {}, b"Service Unavailable")

        # when/then
        with self.assertRaises(Exception) as context:
            with retry_task_on_esi_error(self.task):
                raise exc

        # Verify retry was called
        self.assertEqual(str(context.exception), "Retry called")
        self.task.retry.assert_called_once()
        call_kwargs = self.task.retry.call_args[1]
        self.assertEqual(call_kwargs["countdown"], 63)

    @patch("skillfarm.providers.random.uniform")
    def test_should_retry_on_http_504_error(self, mock_random):
        """
        Test should retry task on HTTP 504 Gateway Timeout error.
        """
        # given
        mock_random.return_value = 2.0  # Fixed jitter for testing
        exc = HTTPServerError(504, {}, b"Gateway Timeout")

        # when/then
        with self.assertRaises(Exception) as context:
            with retry_task_on_esi_error(self.task):
                raise exc

        # Verify retry was called
        self.assertEqual(str(context.exception), "Retry called")
        self.task.retry.assert_called_once()
        call_kwargs = self.task.retry.call_args[1]
        self.assertEqual(call_kwargs["countdown"], 62)

    def test_should_not_retry_on_http_404_error(self):
        """
        Test should not retry task on HTTP 404 error (client error).
        """
        # given
        exc = HTTPClientError(404, {}, b"Not Found")

        # when/then
        with self.assertRaises(HTTPClientError) as context:
            with retry_task_on_esi_error(self.task):
                raise exc

        # Verify retry was NOT called
        self.task.retry.assert_not_called()
        self.assertEqual(context.exception.status_code, 404)

    def test_should_not_retry_on_http_400_error(self):
        """
        Test should not retry task on HTTP 400 error (client error).
        """
        # given
        exc = HTTPClientError(400, {}, b"Bad Request")

        # when/then
        with self.assertRaises(HTTPClientError) as context:
            with retry_task_on_esi_error(self.task):
                raise exc

        # Verify retry was NOT called
        self.task.retry.assert_not_called()
        self.assertEqual(context.exception.status_code, 400)

    @patch("skillfarm.providers.random.uniform")
    def test_should_apply_backoff_jitter_on_retries(self, mock_random):
        """
        Test should apply exponential backoff jitter based on retry count.
        """
        # given
        mock_random.return_value = 4.0
        self.task.request.retries = 2  # Third attempt
        reset_time = 60.0
        exc = ESIErrorLimitException(reset_time)

        # when/then
        with self.assertRaises(Exception):
            with retry_task_on_esi_error(self.task):
                raise exc

        # Verify countdown uses exponential backoff
        call_kwargs = self.task.retry.call_args[1]
        self.assertEqual(call_kwargs["countdown"], 76)

    def test_should_pass_through_on_success(self):
        """
        Test should pass through when no exception is raised.
        """
        # when
        with retry_task_on_esi_error(self.task):
            result = "success"

        # then
        self.assertEqual(result, "success")
        self.task.retry.assert_not_called()

    def test_should_pass_through_unhandled_exceptions(self):
        """
        Test should pass through exceptions that are not ESI-related.
        """
        # given
        exc = ValueError("Some other error")

        # when/then
        with self.assertRaises(ValueError) as context:
            with retry_task_on_esi_error(self.task):
                raise exc

        # Verify retry was NOT called
        self.task.retry.assert_not_called()
        self.assertEqual(str(context.exception), "Some other error")


class TestESIProvider(NoSocketsTestCase):
    @patch("skillfarm.providers.ItemType.objects.bulk_create")
    @patch("skillfarm.providers.ItemGroup.objects.all")
    @patch("skillfarm.providers.ItemType.objects.filter")
    def test_should_create_missing_group_before_bulk_insert(
        self,
        mock_filter,
        mock_groups_all,
        mock_bulk_create,
    ):
        # given
        mock_existing = MagicMock()
        mock_existing.values_list.return_value = []
        mock_existing.__iter__.return_value = iter([])
        mock_filter.return_value = mock_existing

        mock_groups_all.return_value.values_list.return_value = []

        group_type = ItemGroup(id=1210, name="Test Group")

        type_1 = ItemType(id=3300, name="Test Type 1", group=group_type)
        type_2 = ItemType(id=3301, name="Test Type 2", group=group_type)
        mock_bulk_create.return_value = [type_1, type_2]

        # when
        with (
            patch.object(esi, "_get_type", side_effect=[type_1, type_2]),
            patch.object(
                esi,
                "get_group_or_create_from_esi",
                return_value=(MagicMock(), True),
            ) as mock_get_group,
        ):
            result = esi.bulk_type_get_or_create_esi([3300, 3301])

        # then
        mock_get_group.assert_called_once_with(1210)
        mock_bulk_create.assert_called_once_with([type_1, type_2])
        self.assertEqual(result, [type_1, type_2])

    @patch("skillfarm.providers.ItemType.objects.bulk_create")
    @patch("skillfarm.providers.ItemGroup.objects.all")
    @patch("skillfarm.providers.ItemType.objects.filter")
    def test_should_not_fetch_group_when_already_existing(
        self,
        mock_filter,
        mock_groups_all,
        _,
    ):
        # given
        mock_existing = MagicMock()
        mock_existing.values_list.return_value = []
        mock_existing.__iter__.return_value = iter([])
        mock_filter.return_value = mock_existing

        mock_groups_all.return_value.values_list.return_value = [1210]

        group_type = ItemGroup(id=1210, name="Test Group")
        type_obj = ItemType(id=3300, name="Test Type 1", group=group_type)

        # when
        with (
            patch.object(esi, "_get_type", return_value=type_obj),
            patch.object(esi, "get_group_or_create_from_esi") as mock_get_group,
        ):
            esi.bulk_type_get_or_create_esi([3300])

        # then
        mock_get_group.assert_not_called()

    @patch("skillfarm.providers.esi._get_type")
    @patch("skillfarm.providers.esi.get_group_or_create_from_esi")
    @patch("skillfarm.providers.ItemType.objects.update_or_create")
    @patch("skillfarm.providers.ItemType.objects.get")
    def test_should_get_type_or_create_from_esi(
        self,
        mock_item_type_get,
        mock_update_or_create,
        mock_get_group,
        mock_get_type,
    ):
        # given
        mock_item_type_get.side_effect = ItemType.DoesNotExist

        group = ItemGroup(id=1210, name="Test Group")
        mock_get_group.return_value = (group, True)

        type_obj = ItemType(id=3300, name="Test Type 1", group=group)
        mock_get_type.return_value = type_obj
        mock_update_or_create.return_value = (type_obj, True)

        # when
        result, created = esi.get_type_or_create_from_esi(3300)

        # then
        mock_item_type_get.assert_called_once_with(id=3300)
        mock_get_type.assert_called_once_with(type_id=3300)
        mock_get_group.assert_called_once_with(group.id)
        mock_update_or_create.assert_called_once()
        self.assertEqual(result, type_obj)
        self.assertTrue(created)

    @patch("skillfarm.providers.esi._get_type")
    @patch("skillfarm.providers.esi.get_group_or_create_from_esi")
    @patch("skillfarm.providers.ItemType.objects.get")
    def test_get_type_or_create_from_esi_should_handle_general_error(
        self,
        mock_item_type_get,
        mock_get_group,
        mock_get_type,
    ):
        # given
        mock_item_type_get.side_effect = ItemType.DoesNotExist
        mock_get_type.side_effect = Exception("Some other error")

        # when/then
        with self.assertRaises(Exception) as context:
            esi.get_type_or_create_from_esi(3300)

        self.assertEqual(str(context.exception), "Some other error")
