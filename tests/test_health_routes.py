from unittest.mock import AsyncMock, patch

from app.core.constants import APP_VERSION


def test_health_check_returns_liveness_payload(client):
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json()["status"] == "healthy"
    assert response.json()["version"] == APP_VERSION


def test_readiness_returns_ready_when_dependencies_are_available(client):
    storage_service = AsyncMock()
    storage_service.is_available.return_value = True

    with (
        patch("app.api.routes.health.is_database_available", new=AsyncMock(return_value=True)),
        patch("app.api.routes.health.storage_service", storage_service),
    ):
        response = client.get("/ready")

    assert response.status_code == 200
    assert response.json()["status"] == "ready"
    assert response.json()["database"] == "available"
    assert response.json()["storage"] == "available"


def test_readiness_returns_503_when_a_dependency_is_unavailable(client):
    storage_service = AsyncMock()
    storage_service.is_available.return_value = False

    with (
        patch("app.api.routes.health.is_database_available", new=AsyncMock(return_value=True)),
        patch("app.api.routes.health.storage_service", storage_service),
    ):
        response = client.get("/ready")

    assert response.status_code == 503
    assert response.json()["detail"]["status"] == "not_ready"
    assert response.json()["detail"]["database"] == "available"
    assert response.json()["detail"]["storage"] == "unavailable"
