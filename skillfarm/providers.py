"""Shared ESI client for Skillfarm."""

# Standard Library
import logging
import random
from contextlib import contextmanager
from http import HTTPStatus

# Third Party
from aiopenapi3 import RequestError
from celery import Task

# Django
from django.core.exceptions import ObjectDoesNotExist

# Alliance Auth
from allianceauth.services.hooks import get_extension_logger
from esi.exceptions import (
    ESIBucketLimitException,
    ESIErrorLimitException,
    HTTPServerError,
)
from esi.openapi_clients import ESIClientProvider

# Alliance Auth (External Libs)
from eve_sde.models.types import ItemCategory, ItemGroup, ItemType

# AA Skillfarm
from skillfarm import (
    __app_name_useragent__,
    __esi_compatibility_date__,
    __github_url__,
    __operations__,
    __title__,
    __version__,
)


class OpenAPI(ESIClientProvider):
    """Custom ESI Client Provider for Skillfarm."""

    def _get_type(self, type_id: int):
        _type = self.client.Universe.GetUniverseTypesTypeId(type_id=type_id).result(
            use_etag=False
        )

        eve_type = ItemType(
            id=type_id,
            name=_type.name,
            group_id=_type.group_id,
            capacity=_type.capacity,
            description=_type.description,
            icon_id=_type.icon_id,
            mass=_type.mass,
            portion_size=_type.portion_size,
            radius=_type.radius,
            published=_type.published,
            volume=_type.volume,
        )
        return eve_type

    def _get_category(self, category_id: int):
        _category = self.client.Universe.GetUniverseCategoriesCategoryId(
            category_id=category_id
        ).result(use_etag=False)

        category = ItemCategory(
            id=category_id,
            name=_category.name,
            published=_category.published,
        )
        return category

    def _get_group(self, group_id: int):
        _group = self.client.Universe.GetUniverseGroupsGroupId(
            group_id=group_id
        ).result(use_etag=False)

        group = ItemGroup(
            id=group_id,
            name=_group.name,
            category_id=_group.category_id,
            published=_group.published,
        )
        return group

    def get_type_or_create_from_esi(self, eve_id: int):
        """Get or create an EveType by its ESI ID."""
        try:
            eve_type = ItemType.objects.get(id=eve_id)
            created = False
        except ObjectDoesNotExist:
            eve_type, created = self.update_type_or_create_from_esi(eve_id)
        return eve_type, created

    def update_type_or_create_from_esi(self, eve_id: int):
        """Update or create an EveType by its ESI ID."""
        try:
            response = esi._get_type(type_id=eve_id)
            group, created = self.get_group_or_create_from_esi(response.group_id)
            eve_type, created = ItemType.objects.update_or_create(
                id=eve_id,
                defaults={
                    "name": response.name,
                    "group": group,
                    "capacity": response.capacity,
                    "description": response.description,
                    "icon_id": response.icon_id,
                    "mass": response.mass,
                    "portion_size": response.portion_size,
                    "radius": response.radius,
                    "published": response.published,
                    "volume": response.volume,
                },
            )
        except Exception as e:  # pylint: disable=broad-exception-caught
            logger.error("ESI Error for type ID %s: %s", eve_id, e)
            raise e
        return eve_type, created

    def bulk_type_get_or_create_esi(self, eve_ids):
        """
        Bulk get or create EveTypes by their ESI IDs.
        """
        _existing_types = ItemType.objects.filter(id__in=eve_ids)
        _existing_type_ids = set(_existing_types.values_list("id", flat=True))
        _current_groups_ids = set(ItemGroup.objects.all().values_list("id", flat=True))

        new_type_ids = [
            eve_id for eve_id in eve_ids if eve_id not in _existing_type_ids
        ]

        new_types = []
        for eve_id in new_type_ids:
            try:
                response = self._get_type(eve_id)

                if response.group_id not in _current_groups_ids:
                    self.get_group_or_create_from_esi(response.group_id)
                    _current_groups_ids.add(response.group_id)
                new_types.append(response)
            except Exception as e:  # pylint: disable=broad-exception-caught
                logger.error("ESI Error for type ID %s: %s", eve_id, e)
                continue

        created_types = ItemType.objects.bulk_create(new_types)
        return list(_existing_types) + created_types

    def get_group_or_create_from_esi(self, group_id: int):
        """Get or create an EveGroup by its ESI ID."""
        try:
            group = ItemGroup.objects.get(id=group_id)
            created = False
        except ObjectDoesNotExist:
            group, created = self.update_group_or_create_from_esi(group_id)
        return group, created

    def update_group_or_create_from_esi(self, group_id: int):
        """Update or create an EveGroup by its ESI ID."""
        try:
            response = self._get_group(group_id=group_id)
            category, created = self.get_category_or_create_from_esi(
                response.category_id
            )
            group, created = ItemGroup.objects.update_or_create(
                id=group_id,
                defaults={
                    "name": response.name,
                    "category": category,
                    "published": response.published,
                },
            )
        except Exception as e:  # pylint: disable=broad-exception-caught
            logger.error("ESI Error for group ID %s: %s", group_id, e)
            raise e
        return group, created

    def get_category_or_create_from_esi(self, category_id: int):
        """Get or create an EveCategory by its ESI ID."""
        try:
            category = ItemCategory.objects.get(id=category_id)
            created = False
        except ObjectDoesNotExist:
            category, created = self.update_category_or_create_from_esi(category_id)
        return category, created

    def update_category_or_create_from_esi(self, category_id: int):
        """Update or create an EveCategory by its ESI ID."""
        try:
            response = self._get_category(category_id=category_id)
            category, created = ItemCategory.objects.update_or_create(
                id=category_id,
                defaults={
                    "name": response.name,
                    "published": response.published,
                },
            )
        except Exception as e:  # pylint: disable=broad-exception-caught
            logger.error("ESI Error for category ID %s: %s", category_id, e)
            raise e
        return category, created


esi = OpenAPI(
    compatibility_date=__esi_compatibility_date__,
    ua_appname=__app_name_useragent__,
    ua_version=__version__,
    ua_url=__github_url__,
    operations=__operations__,
)


class AppLogger(logging.LoggerAdapter):
    """
    Custom logger adapter that adds a prefix to log messages.

    Taken from the `allianceauth-app-utils` package.
    Credits to: Erik Kalkoken
    """

    def __init__(self, my_logger, prefix):
        """
        Initializes the AppLogger with a logger and a prefix.

        :param my_logger: Logger instance
        :type my_logger: logging.Logger
        :param prefix: Prefix string to add to log messages
        :type prefix: str
        """

        super().__init__(my_logger, {})

        self.prefix = prefix

    def process(self, msg, kwargs):
        """
        Prepares the log message by adding the prefix.

        :param msg: Original log message
        :type msg: str
        :param kwargs: Additional keyword arguments for logging
        :type kwargs: dict
        :return: Tuple of modified message and kwargs
        :rtype: tuple
        """
        return f"[{self.prefix}] {msg}", kwargs


logger = AppLogger(my_logger=get_extension_logger(__name__), prefix=__title__)


@contextmanager
def retry_task_on_esi_error(task: Task):
    """Retry Task when a ESI error occurs.

    Taken from the `allianceauth-app-utils` package.
    Credits to: Erik Kalkoken

    Retries on:
    - Error limits reached (ESIErrorLimitException)
    - Rate limit errors (ESIBucketLimitException)
    - HTTPError with status codes 502, 503, 504 (server errors)

    :param task: Celery Task instance
    :return: Context manager that retries the task on ESI errors.

    """

    def retry(exc: Exception, retry_after: float, issue: str):
        backoff_jitter = int(random.uniform(2, 5) ** task.request.retries)
        countdown = retry_after + backoff_jitter
        logger.warning(
            "ESI Error encountered: %s. Retrying after %.2f seconds. Issue: %s",
            str(exc),
            countdown,
            issue,
        )
        raise task.retry(countdown=countdown, exc=exc)

    try:
        yield
    except ESIErrorLimitException as exc:
        retry(exc, exc.reset, "ESI Error Limit Reached")
    except ESIBucketLimitException as exc:
        retry(exc, exc.reset, f"ESI Bucket Limit Reached for {exc.bucket}")
    except HTTPServerError as exc:
        if exc.status_code in [
            HTTPStatus.BAD_GATEWAY,
            HTTPStatus.SERVICE_UNAVAILABLE,
            HTTPStatus.GATEWAY_TIMEOUT,
        ]:
            retry(exc, 60, f"ESI seems to be down (HTTP {exc.status_code})")
        raise exc
    except RequestError as exc:
        retry(exc, 60, "Request Error")
