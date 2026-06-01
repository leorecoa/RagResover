import logging
import unittest
import warnings
from unittest.mock import AsyncMock, patch

warnings.filterwarnings(
    "ignore",
    message="Using `httpx` with `starlette.testclient` is deprecated.*",
)

from fastapi.testclient import TestClient

from app.core.app import create_app
from app.core.constants import APP_VERSION


class HealthRoutesTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        logging.getLogger("httpx").setLevel(logging.WARNING)

    def setUp(self):
        self.client = TestClient(create_app())

    def tearDown(self):
        self.client.close()

    def test_health_check_returns_liveness_payload(self):
        response = self.client.get("/health")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["status"], "healthy")
        self.assertEqual(response.json()["version"], APP_VERSION)

    def test_readiness_returns_ready_when_dependencies_are_available(self):
        storage_service = AsyncMock()
        storage_service.is_available.return_value = True

        with (
            patch("app.api.routes.health.is_database_available", new=AsyncMock(return_value=True)),
            patch("app.api.routes.health.storage_service", storage_service),
        ):
            response = self.client.get("/ready")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["status"], "ready")
        self.assertEqual(response.json()["database"], "available")
        self.assertEqual(response.json()["storage"], "available")

    def test_readiness_returns_503_when_a_dependency_is_unavailable(self):
        storage_service = AsyncMock()
        storage_service.is_available.return_value = False

        with (
            patch("app.api.routes.health.is_database_available", new=AsyncMock(return_value=True)),
            patch("app.api.routes.health.storage_service", storage_service),
        ):
            response = self.client.get("/ready")

        self.assertEqual(response.status_code, 503)
        self.assertEqual(response.json()["detail"]["status"], "not_ready")
        self.assertEqual(response.json()["detail"]["database"], "available")
        self.assertEqual(response.json()["detail"]["storage"], "unavailable")
