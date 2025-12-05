"""
Example tests demonstrating usage of the ESI OpenAPI stub system.
"""

# Standard Library
from unittest.mock import patch

# Alliance Auth
from esi.exceptions import HTTPClientError, HTTPNotModified, HTTPServerError

# AA Skillfarm
from skillfarm.tests import NoSocketsTestCase
from skillfarm.tests.testdata.esi_stub_openapi import (
    EsiEndpoint,
    create_esi_client_stub,
)

# Example test data configuration
EXAMPLE_TEST_DATA = {
    "Skills": {
        "GetCharactersCharacterIdSkills": {
            "skills": [
                {"skill_id": 12345, "trained_skill_level": 5, "active_skill_level": 5},
                {"skill_id": 67890, "trained_skill_level": 3, "active_skill_level": 3},
            ],
            "total_sp": 50000000,
            "unallocated_sp": 100000,
        },
        "GetCharactersCharacterIdSkillqueue": [
            {
                "skill_id": 11111,
                "finished_level": 4,
                "queue_position": 0,
                "finish_date": "2025-12-31T23:59:59Z",
                "start_date": "2025-12-01T00:00:00Z",
                "training_start_sp": 100000,
                "level_start_sp": 50000,
                "level_end_sp": 150000,
            },
            {
                "skill_id": 22222,
                "finished_level": 5,
                "queue_position": 1,
                "finish_date": "2026-01-15T12:00:00Z",
                "start_date": "2025-12-31T23:59:59Z",
                "training_start_sp": 200000,
                "level_start_sp": 150000,
                "level_end_sp": 300000,
            },
        ],
    },
    "Character": {
        "GetCharactersCharacterId": {
            "character_id": 12345678,
            "name": "Test Character",
            "corporation_id": 98765432,
            "birthday": "2015-03-24T11:37:00Z",
        },
    },
}

# Example endpoints for basic tests
EXAMPLE_ENDPOINTS = [
    EsiEndpoint("Character", "GetCharactersCharacterId", "character_id"),
    EsiEndpoint("Skills", "GetCharactersCharacterIdSkills", "character_id"),
    EsiEndpoint("Skills", "GetCharactersCharacterIdSkillqueue", "character_id"),
]


class TestEsiStubUsage(NoSocketsTestCase):
    """Example tests showing how to use the ESI stub system."""

    def test_stub_with_result_method(self):
        """Test using the stub with result() method for single results."""
        # Create a stub with example data and endpoints
        stub = create_esi_client_stub(EXAMPLE_TEST_DATA, endpoints=EXAMPLE_ENDPOINTS)

        # Simulate an ESI call that returns a single result
        operation = stub.Character.GetCharactersCharacterId(character_id=12345678)
        result = operation.result()

        # Verify the data - now using attributes instead of dict keys
        self.assertEqual(result.character_id, 12345678)
        self.assertEqual(result.name, "Test Character")
        self.assertEqual(result.corporation_id, 98765432)

    def test_stub_with_results_method(self):
        """Test using the stub with results() method for list results."""
        # Create a stub with example data and endpoints
        stub = create_esi_client_stub(EXAMPLE_TEST_DATA, endpoints=EXAMPLE_ENDPOINTS)

        # Simulate an ESI call that returns a list of results
        operation = stub.Skills.GetCharactersCharacterIdSkillqueue(
            character_id=12345678
        )
        results = operation.results()

        # Verify the data - now using attributes
        self.assertIsInstance(results, list)
        self.assertEqual(len(results), 2)
        self.assertEqual(results[0].skill_id, 11111)
        self.assertEqual(results[1].skill_id, 22222)

    def test_stub_with_custom_data(self):
        """Test creating a stub with custom test data."""
        # Define custom test data
        custom_data = {
            "Skills": {
                "GetCharactersCharacterIdSkills": {
                    "skills": [
                        {
                            "skill_id": 99999,
                            "trained_skill_level": 5,
                            "active_skill_level": 5,
                        }
                    ],
                    "total_sp": 1000000,
                    "unallocated_sp": 0,
                }
            }
        }

        # Define endpoints
        endpoints = [
            EsiEndpoint("Skills", "GetCharactersCharacterIdSkills", "character_id"),
        ]

        # Create stub with custom data and endpoints
        stub = create_esi_client_stub(custom_data, endpoints=endpoints)

        # Use the stub
        operation = stub.Skills.GetCharactersCharacterIdSkills(character_id=12345)
        result = operation.result()

        # Verify custom data is returned - using attributes
        self.assertEqual(result.total_sp, 1000000)
        self.assertEqual(len(result.skills), 1)
        self.assertEqual(result.skills[0].skill_id, 99999)

    @patch("skillfarm.providers.esi")
    def test_stub_integration_with_mock(self, mock_esi):
        """Test integrating the stub with mock.patch."""
        # Create a stub with endpoints
        stub = create_esi_client_stub(EXAMPLE_TEST_DATA, endpoints=EXAMPLE_ENDPOINTS)

        # Make mock.client return our stub
        type(mock_esi).client = property(lambda self: stub)

        # Now when code calls esi.client, it will get our stub
        # Verify it works
        self.assertEqual(mock_esi.client, stub)

    def test_stub_with_nested_result(self):
        """Test stub with nested data structures."""
        stub = create_esi_client_stub(EXAMPLE_TEST_DATA, endpoints=EXAMPLE_ENDPOINTS)

        operation = stub.Skills.GetCharactersCharacterIdSkills(character_id=12345)
        result = operation.result()

        # Verify nested structure - using attributes
        self.assertTrue(hasattr(result, "skills"))
        self.assertIsInstance(result.skills, list)
        self.assertEqual(result.skills[0].skill_id, 12345)

    def test_stub_with_dynamic_data(self):
        """Test stub with callable/dynamic test data."""

        def dynamic_skill_data(**kwargs):
            """Return dynamic data based on input."""
            character_id = kwargs.get("character_id", 0)
            return {
                "total_sp": character_id * 1000,  # SP based on character ID
                "skills": [],
                "unallocated_sp": 0,
            }

        # Create stub with callable data
        custom_data = {
            "Skills": {
                "GetCharactersCharacterIdSkills": dynamic_skill_data,
            }
        }

        endpoints = [
            EsiEndpoint("Skills", "GetCharactersCharacterIdSkills", "character_id"),
        ]

        stub = create_esi_client_stub(custom_data, endpoints=endpoints)

        # Call with different character IDs
        op1 = stub.Skills.GetCharactersCharacterIdSkills(character_id=100)
        result1 = op1.result()

        op2 = stub.Skills.GetCharactersCharacterIdSkills(character_id=200)
        result2 = op2.result()

        # Verify dynamic data works - using attributes
        self.assertEqual(result1.total_sp, 100000)
        self.assertEqual(result2.total_sp, 200000)

    def test_stub_missing_method(self):
        """Test stub behavior when method is not registered."""
        endpoints = [
            EsiEndpoint("Skills", "GetCharactersCharacterIdSkills", "character_id"),
        ]
        stub = create_esi_client_stub({"Skills": {}}, endpoints=endpoints)

        # Call a method that isn't registered should raise AttributeError
        with self.assertRaises(AttributeError) as context:
            stub.Skills.SomeUnconfiguredMethod(character_id=12345)

        self.assertIn("not registered", str(context.exception))

    def test_results_wraps_non_list_data(self):
        """Test that results() wraps single items in a list."""
        custom_data = {
            "Test": {
                "SingleItemMethod": {"id": 1, "name": "single"},
            }
        }

        endpoints = [
            EsiEndpoint("Test", "SingleItemMethod", "id"),
        ]

        stub = create_esi_client_stub(custom_data, endpoints=endpoints)
        operation = stub.Test.SingleItemMethod()
        results = operation.results()

        # Single item should be wrapped in list - using attributes
        self.assertIsInstance(results, list)
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].id, 1)

    def test_return_response_parameter(self):
        """Test that result() and results() return tuple when return_response=True."""
        stub = create_esi_client_stub(EXAMPLE_TEST_DATA, endpoints=EXAMPLE_ENDPOINTS)

        # Test with result()
        operation = stub.Character.GetCharactersCharacterId(character_id=12345678)
        data, response = operation.result(return_response=True)
        self.assertEqual(data.character_id, 12345678)
        self.assertEqual(response.status_code, 200)
        self.assertIsInstance(response.headers, dict)

        # Test with results()
        operation = stub.Skills.GetCharactersCharacterIdSkillqueue(
            character_id=12345678
        )
        data, response = operation.results(return_response=True)
        self.assertIsInstance(data, list)
        self.assertEqual(len(data), 2)
        self.assertEqual(response.status_code, 200)

    def test_side_effect_http_not_modified(self):
        """Test that HTTPNotModified exception can be simulated via endpoints."""
        # Define endpoints with side effects
        _endpoints = [
            EsiEndpoint(
                "Character",
                "GetCharactersCharacterId",
                "character_id",
                side_effect=HTTPNotModified(304, {}),
            ),
        ]

        test_data = {
            "Character": {
                "GetCharactersCharacterId": {"character_id": 12345, "name": "Test"}
            }
        }

        stub = create_esi_client_stub(test_data, endpoints=_endpoints)
        operation = stub.Character.GetCharactersCharacterId(character_id=12345)

        # Should raise HTTPNotModified
        with self.assertRaises(HTTPNotModified):
            operation.result()

    def test_side_effect_http_client_error(self):
        """Test that HTTPClientError exception can be simulated via endpoints."""
        _endpoints = [
            EsiEndpoint(
                "Skills",
                "GetCharactersCharacterIdSkills",
                "character_id",
                side_effect=HTTPClientError(404, {}, b"Not Found"),
            ),
        ]

        test_data = {
            "Skills": {"GetCharactersCharacterIdSkills": {"total_sp": 0, "skills": []}}
        }

        stub = create_esi_client_stub(test_data, endpoints=_endpoints)
        operation = stub.Skills.GetCharactersCharacterIdSkills(character_id=12345)

        # Should raise HTTPClientError
        with self.assertRaises(HTTPClientError):
            operation.result()

    def test_side_effect_http_server_error(self):
        """Test that HTTPServerError exception can be simulated via endpoints."""
        _endpoints = [
            EsiEndpoint(
                "Skills",
                "GetCharactersCharacterIdSkillqueue",
                "character_id",
                side_effect=HTTPServerError(500, {}, b"Server Error"),
            ),
        ]

        test_data = {"Skills": {"GetCharactersCharacterIdSkillqueue": []}}

        stub = create_esi_client_stub(test_data, endpoints=_endpoints)
        operation = stub.Skills.GetCharactersCharacterIdSkillqueue(character_id=12345)

        # Should raise HTTPServerError
        with self.assertRaises(HTTPServerError):
            operation.results()

    def test_side_effect_os_error(self):
        """Test that OSError exception can be simulated via endpoints."""
        _endpoints = [
            EsiEndpoint(
                "Character",
                "GetCharactersCharacterId",
                "character_id",
                side_effect=OSError("Connection timeout"),
            ),
        ]

        test_data = {"Character": {"GetCharactersCharacterId": {"character_id": 12345}}}

        stub = create_esi_client_stub(test_data, endpoints=_endpoints)
        operation = stub.Character.GetCharactersCharacterId(character_id=12345)

        # Should raise OSError
        with self.assertRaises(OSError):
            operation.result()

    def test_side_effect_sequential_calls(self):
        """Test that sequential side effects work (first call raises, second returns data)."""
        _endpoints = [
            EsiEndpoint(
                "Skills",
                "GetCharactersCharacterIdSkills",
                "character_id",
                side_effect=[
                    HTTPNotModified(304, {}),
                    HTTPNotModified(304, {}),
                ],
            ),
        ]

        test_data = {
            "Skills": {
                "GetCharactersCharacterIdSkills": {"total_sp": 1000000, "skills": []}
            }
        }

        stub = create_esi_client_stub(test_data, endpoints=_endpoints)
        operation = stub.Skills.GetCharactersCharacterIdSkills(character_id=12345)

        # First call should raise HTTPNotModified
        with self.assertRaises(HTTPNotModified):
            operation.result()

        # Second call should also raise HTTPNotModified
        with self.assertRaises(HTTPNotModified):
            operation.result()

    def test_endpoints_restrict_available_methods(self):
        """Test that only registered endpoints are available when endpoints are provided."""
        _endpoints = [
            EsiEndpoint(
                "Character",
                "GetCharactersCharacterId",
                "character_id",
            ),
        ]

        test_data = {
            "Character": {
                "GetCharactersCharacterId": {"character_id": 12345, "name": "Test"},
                "GetCharactersCharacterIdRoles": {"roles": []},  # Not registered
            }
        }

        stub = create_esi_client_stub(test_data, endpoints=_endpoints)

        # Registered endpoint should work
        operation = stub.Character.GetCharactersCharacterId(character_id=12345)
        result = operation.result()
        self.assertEqual(result.character_id, 12345)

        # Non-registered endpoint should raise AttributeError
        with self.assertRaises(AttributeError) as context:
            stub.Character.GetCharactersCharacterIdRoles(character_id=12345)

        self.assertIn("not registered", str(context.exception))

    def test_endpoints_restrict_available_categories(self):
        """Test that only categories with registered endpoints are available."""
        _endpoints = [
            EsiEndpoint(
                "Character",
                "GetCharactersCharacterId",
                "character_id",
            ),
        ]

        test_data = {
            "Character": {
                "GetCharactersCharacterId": {"character_id": 12345, "name": "Test"}
            },
            "Skills": {
                "GetCharactersCharacterIdSkills": {
                    "total_sp": 0
                }  # Category not registered
            },
        }

        stub = create_esi_client_stub(test_data, endpoints=_endpoints)

        # Registered category should work
        operation = stub.Character.GetCharactersCharacterId(character_id=12345)
        result = operation.result()
        self.assertEqual(result.name, "Test")

        # Non-registered category should raise AttributeError
        with self.assertRaises(AttributeError) as context:
            stub.Skills.GetCharactersCharacterIdSkills(character_id=12345)

        self.assertIn("not registered", str(context.exception))

    def test_endpoints_are_required(self):
        """Test that endpoints parameter is required."""
        test_data = {
            "Character": {
                "GetCharactersCharacterId": {"character_id": 12345, "name": "Test"}
            }
        }

        # Should raise ValueError when no endpoints provided
        with self.assertRaises(ValueError) as context:
            create_esi_client_stub(test_data)

        self.assertIn("endpoints parameter is required", str(context.exception))

    def test_multiple_endpoints_mixed(self):
        """Test multiple endpoints with and without side effects."""
        _endpoints = [
            EsiEndpoint(
                "Character",
                "GetCharactersCharacterId",
                "character_id",
                side_effect=HTTPNotModified(304, {}),
            ),
            EsiEndpoint(
                "Skills",
                "GetCharactersCharacterIdSkills",
                "character_id",
            ),
        ]

        test_data = {
            "Character": {"GetCharactersCharacterId": {"character_id": 12345}},
            "Skills": {
                "GetCharactersCharacterIdSkills": {"total_sp": 5000000, "skills": []}
            },
        }

        stub = create_esi_client_stub(test_data, endpoints=_endpoints)

        # Character endpoint should raise exception
        char_op = stub.Character.GetCharactersCharacterId(character_id=12345)
        with self.assertRaises(HTTPNotModified):
            char_op.result()

        # Skills endpoint should return normal data
        skills_op = stub.Skills.GetCharactersCharacterIdSkills(character_id=12345)
        skills_result = skills_op.result()
        self.assertEqual(skills_result.total_sp, 5000000)
