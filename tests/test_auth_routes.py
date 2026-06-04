import app.api.dependencies.auth as auth_dependency
import app.api.routes.auth as auth_route


def token_payload():
    return {
        "access_token": "jwt-token",
        "token_type": "bearer",
        "expires_in": 3600,
        "user": {
            "user_id": "11111111-1111-1111-1111-111111111111",
            "email": "owner@example.com",
            "full_name": "Owner",
            "organizations": [
                {
                    "organization_id": "22222222-2222-2222-2222-222222222222",
                    "role": "owner",
                }
            ],
        },
    }


def test_register_returns_access_token(client_with_fake_db, monkeypatch):
    async def fake_register(**kwargs):
        assert kwargs["email"] == "owner@example.com"
        assert kwargs["password"] == "super-secret"
        assert kwargs["full_name"] == "Owner"
        assert kwargs["organization_name"] == "Acme"
        return token_payload()

    monkeypatch.setattr(auth_route, "register_user_with_organization", fake_register)

    response = client_with_fake_db.post(
        "/auth/register",
        json={
            "email": "owner@example.com",
            "password": "super-secret",
            "full_name": "Owner",
            "organization_name": "Acme",
        },
    )

    assert response.status_code == 201
    assert response.json()["access_token"] == "jwt-token"
    assert response.json()["user"]["organizations"][0]["role"] == "owner"


def test_login_returns_access_token(client_with_fake_db, monkeypatch):
    async def fake_login(**kwargs):
        assert kwargs["email"] == "owner@example.com"
        assert kwargs["password"] == "super-secret"
        assert kwargs["organization_id"] == "22222222-2222-2222-2222-222222222222"
        return token_payload()

    monkeypatch.setattr(auth_route, "authenticate_user", fake_login)

    response = client_with_fake_db.post(
        "/auth/login",
        json={
            "email": "owner@example.com",
            "password": "super-secret",
            "organization_id": "22222222-2222-2222-2222-222222222222",
        },
    )

    assert response.status_code == 200
    assert response.json()["token_type"] == "bearer"


def test_me_returns_current_jwt_context(app, client):
    async def fake_context():
        return auth_dependency.TenantContext(
            tenant_id="22222222-2222-2222-2222-222222222222",
            is_anonymous=False,
            user_id="11111111-1111-1111-1111-111111111111",
            email="owner@example.com",
            full_name="Owner",
            roles=frozenset({"owner"}),
            memberships={"22222222-2222-2222-2222-222222222222": "owner"},
        )

    app.dependency_overrides[auth_route.require_authenticated_context] = fake_context

    response = client.get("/auth/me")

    assert response.status_code == 200
    assert response.json() == {
        "user_id": "11111111-1111-1111-1111-111111111111",
        "email": "owner@example.com",
        "full_name": "Owner",
        "organizations": [
            {
                "organization_id": "22222222-2222-2222-2222-222222222222",
                "role": "owner",
            }
        ],
    }


def test_me_requires_authenticated_context(client):
    response = client.get("/auth/me")

    assert response.status_code == 401
