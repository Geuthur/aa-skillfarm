"""Tests that the whole API requires a login and `basic_access`."""

# Standard Library
import re
from http import HTTPStatus
from unittest.mock import patch

# AA Skillfarm
from skillfarm import __app_name__
from skillfarm.api import api
from skillfarm.models.general import General
from skillfarm.tests import AuthTestCase
from skillfarm.tests.testdata.skillfarm import UserMainFactory

TASK_PATH = "skillfarm.tasks"
BASIC_ACCESS = f"{__app_name__}.basic_access"
HIGHER_PERMISSIONS = [
    f"{__app_name__}.{codename}"
    for codename, _ in General._meta.permissions
    if codename != "basic_access"
]


def _routes() -> list[tuple[str, str]]:
    """Return (method, url) of every route of the API, path parameters replaced by `1`."""
    found = []
    for path, operations in api.get_openapi_schema()["paths"].items():
        for method in operations:
            found.append((method.upper(), re.sub(r"\{[^}]+\}", "1", path)))
    return found


class TestApiAuth(AuthTestCase):
    """
    Basic access is only granted by `basic_access`.

    Higher permissions do not include it: without `basic_access` every
    endpoint answers 403. The tests walk all routes of the API, so a new
    endpoint is covered without any change here.
    """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.routes = _routes()
        cls.users_without_basic_access = {
            "no permission": UserMainFactory(permissions__=[]),
            "all higher permissions": UserMainFactory(permissions__=HIGHER_PERMISSIONS),
        }
        for permission in HIGHER_PERMISSIONS:
            cls.users_without_basic_access[permission] = UserMainFactory(
                permissions__=[permission]
            )

    def setUp(self):
        super().setUp()
        # The routes are called with placeholder ids and an empty body. Endpoints
        # that queue tasks (character update, update-all, update-prices) must not
        # reach Celery from here.
        self.queued_tasks = {}
        for task in ("update_character", "update_all_skillfarm", "update_all_prices"):
            patcher = patch(f"{TASK_PATH}.{task}.apply_async")
            self.queued_tasks[task] = patcher.start()
            self.addCleanup(patcher.stop)

    def _request(self, method: str, url: str, client=None):
        client = client or self.client
        return client.generic(method, url, content_type="application/json")

    def test_api_should_have_routes_and_higher_permissions(self):
        # Expected Result: the tests below must not pass on empty lists
        self.assertTrue(self.routes)
        self.assertTrue(HIGHER_PERMISSIONS)
        for name, user in self.users_without_basic_access.items():
            with self.subTest(user=name):
                self.assertFalse(user.has_perm(BASIC_ACCESS))
        user = self.users_without_basic_access["all higher permissions"]
        for permission in HIGHER_PERMISSIONS:
            with self.subTest(permission=permission):
                self.assertTrue(user.has_perm(permission))

    def test_every_endpoint_should_redirect_to_login_without_login(self):
        # Alliance Auth wraps every hooked URL in `main_character_required`,
        # so a request without login never reaches the API.
        for method, url in self.routes:
            with self.subTest(method=method, url=url):
                # Test Action
                response = self._request(method, url)

                # Expected Result
                self.assertEqual(response.status_code, HTTPStatus.FOUND)
                self.assertIn("/account/login/", response["Location"])

    def test_every_endpoint_should_return_403_without_basic_access(self):
        for name, user in self.users_without_basic_access.items():
            self.client.force_login(user)
            for method, url in self.routes:
                with self.subTest(user=name, method=method, url=url):
                    # Test Action
                    response = self._request(method, url)

                    # Expected Result
                    self.assertEqual(response.status_code, HTTPStatus.FORBIDDEN)
                    self.assertEqual(response.json(), {"error": "Permission Denied"})

        # Expected Result: no request got far enough to queue a task
        for task, apply_async in self.queued_tasks.items():
            with self.subTest(task=task):
                apply_async.assert_not_called()

    def test_every_endpoint_should_pass_with_basic_access(self):
        # Test Data: a superuser passes `has_perm` without the permission
        users = {
            "basic_access and all higher permissions": UserMainFactory(
                permissions__=[BASIC_ACCESS, *HIGHER_PERMISSIONS]
            ),
            "superuser": UserMainFactory(permissions__=[], is_superuser=True),
        }

        for name, user in users.items():
            self.client.force_login(user)
            for method, url in self.routes:
                with self.subTest(user=name, method=method, url=url):
                    # Test Action
                    response = self._request(method, url)

                    # Expected Result: the endpoint itself answers (200, 404, 422, ...)
                    if response.status_code == HTTPStatus.FORBIDDEN:
                        # Superuser-only endpoints refuse with their own message
                        self.assertNotEqual(name, "superuser")
                        self.assertEqual(
                            response.json(),
                            {"error": "Superuser permission required."},
                        )
                    self.assertNotEqual(response.status_code, HTTPStatus.UNAUTHORIZED)

    def test_endpoints_outside_administration_should_pass_with_basic_access_only(
        self,
    ):
        # `basic_access` alone is enough for everything but the Administration,
        # which answers 403 itself without `admin_access` or `corp_access`.
        routes = [
            (method, url)
            for method, url in self.routes
            if "/api/administration/" not in url
        ]
        self.assertTrue(routes)
        self.client.force_login(self.user)

        for method, url in routes:
            with self.subTest(method=method, url=url):
                # Test Action
                response = self._request(method, url)

                # Expected Result
                self.assertNotIn(
                    response.status_code,
                    (HTTPStatus.UNAUTHORIZED, HTTPStatus.FORBIDDEN),
                )

    def test_api_root_should_return_403_without_basic_access(self):
        # The decorator sits on the URLs, so it also covers the root, schema and docs
        self.client.force_login(self.users_without_basic_access["no permission"])

        # Test Action
        response = self.client.get(f"/{__app_name__}/api/")

        # Expected Result
        self.assertEqual(response.status_code, HTTPStatus.FORBIDDEN)

    def test_writing_endpoints_should_return_403_without_csrf_token(self):
        # Test Data
        client = self.client_class(enforce_csrf_checks=True)
        client.force_login(self.user)
        writing = [
            (method, url)
            for method, url in self.routes
            if method not in ("GET", "HEAD", "OPTIONS")
        ]
        self.assertTrue(writing)

        for method, url in writing:
            with self.subTest(method=method, url=url):
                # Test Action
                response = self._request(method, url, client=client)

                # Expected Result
                self.assertEqual(response.status_code, HTTPStatus.FORBIDDEN)
                self.assertEqual(response.json(), {"detail": "CSRF check Failed"})
