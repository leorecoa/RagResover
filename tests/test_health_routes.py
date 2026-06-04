from unittest.mock import AsyncMock, patch

import app.api.routes.metrics as metrics_module
from app.core.constants import APP_VERSION


def test_health_check_returns_liveness_payload(client):
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json()["status"] == "healthy"
    assert response.json()["version"] == APP_VERSION
    assert response.headers["X-Request-ID"]


def test_request_id_header_is_preserved(client):
    response = client.get("/health", headers={"X-Request-ID": "request-test-1"})

    assert response.status_code == 200
    assert response.headers["X-Request-ID"] == "request-test-1"


def test_traceparent_header_is_propagated_with_new_span(client):
    trace_id = "4bf92f3577b34da6a3ce929d0e0e4736"
    response = client.get(
        "/health",
        headers={"traceparent": f"00-{trace_id}-00f067aa0ba902b7-01"},
    )

    assert response.status_code == 200
    returned = response.headers["traceparent"]
    assert returned.startswith(f"00-{trace_id}-")
    assert returned.endswith("-01")
    assert returned != f"00-{trace_id}-00f067aa0ba902b7-01"


def test_traceparent_header_is_generated_when_missing(client):
    response = client.get("/health")

    assert response.status_code == 200
    assert response.headers["traceparent"].count("-") == 3


def test_metrics_endpoint_exposes_request_counters(client):
    client.get("/health")

    response = client.get("/metrics")

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/plain")
    assert "ragresover_http_requests_total" in response.text
    assert 'method="GET",path="/health",status_code="200"' in response.text


def test_metrics_endpoint_can_require_admin_role(client, monkeypatch):
    monkeypatch.setattr(metrics_module.settings, "METRICS_REQUIRE_ADMIN", True)
    monkeypatch.setattr(metrics_module.settings, "API_AUTH_TOKEN", _Secret("expected"))
    monkeypatch.setattr(metrics_module.settings, "ADMIN_ROLE_NAME", "admin")

    missing_token = client.get("/metrics")
    assert missing_token.status_code == 401

    missing_role = client.get(
        "/metrics",
        headers={
            "Authorization": "Bearer expected",
            "X-Tenant-ID": "tenant-admin",
            "X-User-Roles": "viewer",
        },
    )
    assert missing_role.status_code == 403

    response = client.get(
        "/metrics",
        headers={
            "Authorization": "Bearer expected",
            "X-Tenant-ID": "tenant-admin",
            "X-User-ID": "user-admin",
            "X-User-Roles": "admin,viewer",
        },
    )
    assert response.status_code == 200


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


class _Secret:
    def __init__(self, value: str):
        self.value = value

    def get_secret_value(self):
        return self.value
