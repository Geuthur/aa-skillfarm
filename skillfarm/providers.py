"""Shared ESI client for Skillfarm."""

# Standard Library
import logging
import random
from contextlib import contextmanager
from http import HTTPStatus

# Third Party
from aiopenapi3 import RequestError
from celery import Task

# Alliance Auth
from allianceauth.services.hooks import get_extension_logger
from esi.exceptions import (
    ESIBucketLimitException,
    ESIErrorLimitException,
    HTTPServerError,
)
from esi.openapi_clients import ESIClientProvider

# AA Skillfarm
from skillfarm import (
    __app_name_useragent__,
    __characters_operations__,
    __esi_compatibility_date__,
    __github_url__,
    __title__,
    __version__,
)


class OpenAPI(ESIClientProvider):
    """Custom ESI Client Provider for Skillfarm."""

    def _get_type(self, type_id: int):
        # AA Skillfarm
        # pylint: disable=import-outside-toplevel, cyclic-import
        from skillfarm.models.prices import EveType

        _type = self.client.Universe.GetUniverseTypesTypeId(type_id=type_id).result()

        eve_type = EveType(
            name=_type.name,
            type_id=type_id,
            eve_group_id=_type.group_id,
            capacity=_type.capacity,
            description=_type.description,
            icon_id=_type.icon_id,
            mass=_type.mass,
            packaged_volume=_type.packaged_volume,
            portion_size=_type.portion_size,
            radius=_type.radius,
            published=_type.published,
            volume=_type.volume,
        )
        return eve_type

    def _get_category(self, category_id: int):
        # AA Skillfarm
        # pylint: disable=import-outside-toplevel, cyclic-import
        from skillfarm.models.prices import EveCategory

        _category = self.client.Universe.GetUniverseCategoriesCategoryId(
            category_id=category_id
        ).result()

        category = EveCategory(
            category_id=category_id,
            name=_category.name,
        )
        return category

    def _get_group(self, group_id: int):
        # AA Skillfarm
        # pylint: disable=import-outside-toplevel, cyclic-import
        from skillfarm.models.prices import EveGroup

        _group = self.client.Universe.GetUniverseGroupsGroupId(
            group_id=group_id
        ).result()

        group = EveGroup(
            group_id=group_id,
            name=_group.name,
        )
        return group


esi = OpenAPI(
    compatibility_date=__esi_compatibility_date__,
    ua_appname=__app_name_useragent__,
    ua_version=__version__,
    ua_url=__github_url__,
    operations=__characters_operations__,
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
