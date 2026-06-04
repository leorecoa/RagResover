import app.api.dependencies.auth as auth_dependency
import app.api.routes.organizations as organizations_route
from app.services.organizations import ensure_manager


def owner_context():
    return auth_dependency.TenantContext(
        tenant_id="22222222-2222-2222-2222-222222222222",
        is_anonymous=False,
        user_id="11111111-1111-1111-1111-111111111111",
        email="owner@example.com",
        full_name="Owner",
        roles=frozenset({"owner"}),
        memberships={"22222222-2222-2222-2222-222222222222": "owner"},
    )


def test_get_current_organization_returns_settings(app, client_with_fake_db, monkeypatch):
    async def fake_context():
        return owner_context()

    async def fake_get_current_organization(**kwargs):
        assert kwargs["context"].tenant_id == "22222222-2222-2222-2222-222222222222"
        return {
            "id": "22222222-2222-2222-2222-222222222222",
            "name": "Acme",
            "current_user_role": "owner",
        }

    app.dependency_overrides[organizations_route.require_authenticated_context] = fake_context
    monkeypatch.setattr(
        organizations_route,
        "get_current_organization",
        fake_get_current_organization,
    )

    response = client_with_fake_db.get("/organizations/current")

    assert response.status_code == 200
    assert response.json()["name"] == "Acme"
    assert response.json()["current_user_role"] == "owner"


def test_update_current_organization_uses_request_name(app, client_with_fake_db, monkeypatch):
    async def fake_context():
        return owner_context()

    async def fake_update_current_organization(**kwargs):
        assert kwargs["name"] == "Acme Legal"
        return {
            "id": "22222222-2222-2222-2222-222222222222",
            "name": "Acme Legal",
            "current_user_role": "owner",
        }

    app.dependency_overrides[organizations_route.require_authenticated_context] = fake_context
    monkeypatch.setattr(
        organizations_route,
        "update_current_organization",
        fake_update_current_organization,
    )

    response = client_with_fake_db.patch(
        "/organizations/current",
        json={"name": "Acme Legal"},
    )

    assert response.status_code == 200
    assert response.json()["name"] == "Acme Legal"


def test_invite_member_creates_pending_invitation(app, client_with_fake_db, monkeypatch):
    async def fake_context():
        return owner_context()

    async def fake_invite_member(**kwargs):
        assert kwargs["email"] == "analyst@example.com"
        assert kwargs["role"] == "member"
        return {
            "id": "33333333-3333-3333-3333-333333333333",
            "organization_id": "22222222-2222-2222-2222-222222222222",
            "email": "analyst@example.com",
            "role": "member",
            "invited_by_user_id": "11111111-1111-1111-1111-111111111111",
            "status": "pending",
            "created_at": "2026-06-04T12:00:00",
        }

    app.dependency_overrides[organizations_route.require_authenticated_context] = fake_context
    monkeypatch.setattr(organizations_route, "invite_member", fake_invite_member)

    response = client_with_fake_db.post(
        "/organizations/current/invitations",
        json={"email": "analyst@example.com", "role": "member"},
    )

    assert response.status_code == 201
    assert response.json()["status"] == "pending"


def test_list_members_and_update_role(app, client_with_fake_db, monkeypatch):
    async def fake_context():
        return owner_context()

    async def fake_list_current_organization_members(**kwargs):
        return [
            {
                "user_id": "11111111-1111-1111-1111-111111111111",
                "email": "owner@example.com",
                "full_name": "Owner",
                "role": "owner",
                "created_at": "2026-06-04T12:00:00",
            }
        ]

    async def fake_update_member_role(**kwargs):
        assert kwargs["user_id"] == "44444444-4444-4444-4444-444444444444"
        assert kwargs["role"] == "viewer"
        return {
            "user_id": "44444444-4444-4444-4444-444444444444",
            "email": "viewer@example.com",
            "full_name": None,
            "role": "viewer",
            "created_at": "2026-06-04T12:00:00",
        }

    app.dependency_overrides[organizations_route.require_authenticated_context] = fake_context
    monkeypatch.setattr(
        organizations_route,
        "list_current_organization_members",
        fake_list_current_organization_members,
    )
    monkeypatch.setattr(organizations_route, "update_member_role", fake_update_member_role)

    members_response = client_with_fake_db.get("/organizations/current/members")
    role_response = client_with_fake_db.patch(
        "/organizations/current/members/44444444-4444-4444-4444-444444444444",
        json={"role": "viewer"},
    )

    assert members_response.status_code == 200
    assert members_response.json()["members"][0]["role"] == "owner"
    assert role_response.status_code == 200
    assert role_response.json()["members"][0]["role"] == "viewer"


def test_viewer_cannot_manage_organization():
    context = auth_dependency.TenantContext(
        tenant_id="22222222-2222-2222-2222-222222222222",
        is_anonymous=False,
        user_id="55555555-5555-5555-5555-555555555555",
        roles=frozenset({"viewer"}),
    )

    try:
        ensure_manager(context)
    except Exception as exc:
        assert getattr(exc, "status_code") == 403
    else:
        raise AssertionError("viewer role should not manage organization")
