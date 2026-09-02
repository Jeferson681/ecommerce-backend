from __future__ import annotations

from fastapi.testclient import TestClient

from backend.app.core.database import Base, engine
from backend.app.main import app
from backend.app.modules.auth.tokens import create_access_token

client = TestClient(app)


def setup_module(module: object) -> None:
    """Create all tables before running tests."""
    Base.metadata.create_all(bind=engine)


def teardown_module(module: object) -> None:
    """Drop all tables after running tests."""
    Base.metadata.drop_all(bind=engine)


def test_post_auth_token_with_valid_credentials() -> None:
    """Test login endpoint with valid credentials."""
    test_password = "Password123!"
    create_resp = client.post(
        "/users",
        json={
            "first_name": "Ana",
            "last_name": "Silva",
            "email": "ana@mail.com",
            "password": test_password,
        },
    )
    assert create_resp.status_code == 201

    payload = {"email": "ana@mail.com", "password": test_password}
    resp = client.post("/auth/token", json=payload)

    assert resp.status_code == 200
    body = resp.json()
    assert "access_token" in body
    assert "refresh_token" in body
    assert body["token_type"] == "bearer"
    assert body["expires_in"] is not None


def test_post_auth_token_with_invalid_email() -> None:
    """Test login endpoint with non-existent email."""
    payload = {"email": "nonexistent@mail.com", "password": "Password123!"}
    resp = client.post("/auth/token", json=payload)

    assert resp.status_code == 401


def test_post_auth_token_with_invalid_password() -> None:
    """Test login endpoint with incorrect password."""
    create_resp = client.post(
        "/users",
        json={
            "first_name": "João",
            "last_name": "Santos",
            "email": "joao@mail.com",
            "password": "Password123!",
        },
    )
    assert create_resp.status_code == 201

    payload = {"email": "joao@mail.com", "password": "WrongPassword"}
    resp = client.post("/auth/token", json=payload)

    assert resp.status_code == 401


def test_expired_access_token_signals_expiry_via_www_authenticate() -> None:
    """Expired access token -> 401 with the RFC 6750 invalid_token signal.

    This header is the only contract signal that authorizes the client to
    attempt the refresh-token flow.
    """
    test_password = "Password123!"
    create_resp = client.post(
        "/users",
        json={
            "first_name": "Eva",
            "last_name": "Expirada",
            "email": "eva-expired@mail.com",
            "password": test_password,
        },
    )
    assert create_resp.status_code == 201
    user_id = create_resp.json()["id"]

    expired_token = create_access_token({"sub": str(user_id)}, expires_delta=-1)
    resp = client.get("/users/me", headers={"Authorization": f"Bearer {expired_token}"})

    assert resp.status_code == 401
    www_auth = resp.headers.get("WWW-Authenticate")
    assert www_auth is not None
    assert 'error="invalid_token"' in www_auth


def test_invalid_access_token_does_not_signal_expiry() -> None:
    """A malformed token must NOT carry the expiry signal (no refresh)."""
    resp = client.get("/users/me", headers={"Authorization": "Bearer not-a-real-jwt"})
    assert resp.status_code == 401
    assert resp.headers.get("WWW-Authenticate") is None


def test_login_failure_does_not_signal_token_expiry() -> None:
    """Invalid-credentials 401 must NOT carry the expiry signal."""
    payload = {"email": "no-such-user-401@mail.com", "password": "Password123!"}
    resp = client.post("/auth/token", json=payload)
    assert resp.status_code == 401
    assert resp.headers.get("WWW-Authenticate") is None


def test_post_auth_logout_with_valid_token() -> None:
    """Test logout endpoint with valid refresh token."""
    test_password = "Password123!"
    create_resp = client.post(
        "/users",
        json={
            "first_name": "Maria",
            "last_name": "Costa",
            "email": "maria@mail.com",
            "password": test_password,
        },
    )
    assert create_resp.status_code == 201

    login_payload = {"email": "maria@mail.com", "password": test_password}
    login_resp = client.post("/auth/token", json=login_payload)
    assert login_resp.status_code == 200

    refresh_token = login_resp.json()["refresh_token"]
    access_token = login_resp.json()["access_token"]

    logout_payload = {"refresh_token": refresh_token}
    logout_resp = client.post(
        "/auth/logout",
        json=logout_payload,
        headers={"Authorization": f"Bearer {access_token}"},
    )

    assert logout_resp.status_code == 204


def test_post_auth_logout_with_invalid_token() -> None:
    """Test logout endpoint with invalid refresh token."""
    payload = {"refresh_token": "invalid_token_12345"}
    resp = client.post("/auth/logout", json=payload)

    assert resp.status_code == 401


def test_post_auth_refresh_with_valid_token() -> None:
    """Test refresh endpoint with valid refresh token."""
    test_password = "Password123!"
    create_resp = client.post(
        "/users",
        json={
            "first_name": "Carlos",
            "last_name": "Oliveira",
            "email": "carlos@mail.com",
            "password": test_password,
        },
    )
    assert create_resp.status_code == 201

    login_payload = {"email": "carlos@mail.com", "password": test_password}
    login_resp = client.post("/auth/token", json=login_payload)
    assert login_resp.status_code == 200

    refresh_token = login_resp.json()["refresh_token"]

    refresh_payload = {"refresh_token": refresh_token}
    refresh_resp = client.post("/auth/refresh", json=refresh_payload)

    assert refresh_resp.status_code == 200
    body = refresh_resp.json()
    assert "access_token" in body
    assert body["refresh_token"] != refresh_token
    assert body["token_type"] == "bearer"
    assert body["expires_in"] is not None


def test_post_auth_refresh_with_invalid_token() -> None:
    """Test refresh endpoint with invalid refresh token."""
    payload = {"refresh_token": "invalid_refresh_token"}
    resp = client.post("/auth/refresh", json=payload)

    assert resp.status_code == 401


def test_get_users_me_with_valid_token() -> None:
    """Test GET /users/me endpoint with valid access token."""
    test_password = "Password123!"
    create_resp = client.post(
        "/users",
        json={
            "first_name": "Patricia",
            "last_name": "Lima",
            "email": "patricia@mail.com",
            "password": test_password,
        },
    )
    assert create_resp.status_code == 201
    created_user = create_resp.json()
    created_user_id = created_user["id"]

    login_payload = {"email": "patricia@mail.com", "password": test_password}
    login_resp = client.post("/auth/token", json=login_payload)
    assert login_resp.status_code == 200

    access_token = login_resp.json()["access_token"]

    headers = {"Authorization": f"Bearer {access_token}"}
    me_resp = client.get("/users/me", headers=headers)

    assert me_resp.status_code == 200
    body = me_resp.json()
    assert body["id"] == created_user_id
    assert body["email"] == "patricia@mail.com"
    assert body["first_name"] == "Patricia"
    assert body["last_name"] == "Lima"


def test_get_users_me_without_token() -> None:
    """Test GET /users/me endpoint without authorization header."""
    resp = client.get("/users/me")

    assert resp.status_code == 401


def test_get_users_me_with_invalid_token() -> None:
    """Test GET /users/me endpoint with invalid access token."""
    headers = {"Authorization": "Bearer invalid_access_token"}
    resp = client.get("/users/me", headers=headers)

    assert resp.status_code == 401


def test_inactive_user_cannot_log_in_or_access_protected_endpoints() -> None:
    password = "Password123!"
    email = "inactive-user@mail.com"
    create_resp = client.post(
        "/users",
        json={
            "first_name": "Inactive",
            "last_name": "User",
            "email": email,
            "password": password,
        },
    )
    assert create_resp.status_code == 201
    user_id = create_resp.json()["id"]

    login_resp = client.post("/auth/token", json={"email": email, "password": password})
    assert login_resp.status_code == 200
    access_token = login_resp.json()["access_token"]

    deactivate_resp = client.patch(
        f"/users/{user_id}",
        json={"is_active": False},
        headers={"Authorization": f"Bearer {access_token}"},
    )
    assert deactivate_resp.status_code == 200

    denied_login = client.post(
        "/auth/token", json={"email": email, "password": password}
    )
    assert denied_login.status_code == 401

    denied_access = client.get(
        "/users/me",
        headers={"Authorization": f"Bearer {access_token}"},
    )
    assert denied_access.status_code == 401


# ===========================================================================
# Refresh Token Rotation — Integration Tests
# ===========================================================================


def _create_and_login(email: str, password: str) -> dict:
    """Helper: create user + return login response json."""
    create_resp = client.post(
        "/users",
        json={
            "first_name": "Test",
            "last_name": "User",
            "email": email,
            "password": password,
        },
    )
    assert create_resp.status_code == 201
    login_resp = client.post(
        "/auth/token",
        json={"email": email, "password": password},
    )
    assert login_resp.status_code == 200
    return login_resp.json()


def test_refresh_rotates_token_new_token_different_from_old() -> None:
    """Refresh must return a NEW refresh token (rotation), not the same one."""
    password = "Password123!"
    login = _create_and_login("rotate1@mail.com", password)

    old_refresh = login["refresh_token"]

    refresh_resp = client.post(
        "/auth/refresh",
        json={"refresh_token": old_refresh},
    )
    assert refresh_resp.status_code == 200
    new_body = refresh_resp.json()

    assert new_body["refresh_token"] != old_refresh
    assert new_body["access_token"] != login["access_token"]
    assert new_body["token_type"] == "bearer"
    assert new_body["expires_in"] is not None


def test_refresh_revokes_old_token_replay_attack_blocked() -> None:
    """After refresh, the OLD refresh token must be blocked (rotation replay protection)."""
    password = "Password123!"
    login = _create_and_login("replay1@mail.com", password)

    old_refresh = login["refresh_token"]

    # First refresh (valid)
    first_refresh = client.post(
        "/auth/refresh",
        json={"refresh_token": old_refresh},
    )
    assert first_refresh.status_code == 200

    # Second refresh with the same old token (replay attack) must fail
    replay_resp = client.post(
        "/auth/refresh",
        json={"refresh_token": old_refresh},
    )
    assert replay_resp.status_code == 401


def test_logout_revokes_token_can_no_longer_refresh() -> None:
    """After logout, the refresh token must be blocked."""
    password = "Password123!"
    login = _create_and_login("logout1@mail.com", password)

    refresh_token = login["refresh_token"]
    access_token = login["access_token"]

    # Logout
    logout_resp = client.post(
        "/auth/logout",
        json={"refresh_token": refresh_token},
        headers={"Authorization": f"Bearer {access_token}"},
    )
    assert logout_resp.status_code == 204

    # Refresh after logout must fail
    refresh_after_logout = client.post(
        "/auth/refresh",
        json={"refresh_token": refresh_token},
    )
    assert refresh_after_logout.status_code == 401


def test_logout_then_login_creates_new_token() -> None:
    """Logout of one session doesn't affect a fresh login.

    User logs in twice (two sessions), then logs out of the first.
    The second session remains valid.
    """
    password = "Password123!"

    # Create user once
    create_resp = client.post(
        "/users",
        json={
            "first_name": "Multi",
            "last_name": "User",
            "email": "multisession1@mail.com",
            "password": password,
        },
    )
    assert create_resp.status_code == 201

    # First session
    login1 = client.post(
        "/auth/token",
        json={"email": "multisession1@mail.com", "password": password},
    )
    assert login1.status_code == 200
    login1_body = login1.json()
    r1 = login1_body["refresh_token"]

    # Second session (same user, new login)
    login2 = client.post(
        "/auth/token",
        json={"email": "multisession1@mail.com", "password": password},
    )
    assert login2.status_code == 200
    login2_body = login2.json()
    r2 = login2_body["refresh_token"]

    # Logout from first session
    logout1 = client.post(
        "/auth/logout",
        json={"refresh_token": r1},
        headers={"Authorization": f"Bearer {login1_body['access_token']}"},
    )
    assert logout1.status_code == 204

    # Second session should still work for refresh
    refresh_resp = client.post(
        "/auth/refresh",
        json={"refresh_token": r2},
    )
    assert refresh_resp.status_code == 200


def test_double_refresh_both_tokens_invalid() -> None:
    """After two consecutive refreshes, neither old token should work."""
    password = "Password123!"
    login = _create_and_login("double1@mail.com", password)

    t0 = login["refresh_token"]

    # First refresh
    r1 = client.post("/auth/refresh", json={"refresh_token": t0})
    assert r1.status_code == 200
    t1 = r1.json()["refresh_token"]

    # Second refresh (rotate again)
    r2 = client.post("/auth/refresh", json={"refresh_token": t1})
    assert r2.status_code == 200
    t2 = r2.json()["refresh_token"]

    # None of the old tokens should work
    for stolen_token in [t0, t1]:
        fail_resp = client.post("/auth/refresh", json={"refresh_token": stolen_token})
        assert fail_resp.status_code == 401, (
            f"Token {stolen_token[:20]}... should be blocked"
        )

    # Only the latest token should work
    latest = client.post("/auth/refresh", json={"refresh_token": t2})
    assert latest.status_code == 200


def test_logout_twice_with_same_token_fails() -> None:
    """Logout with an already-revoked token must fail."""
    password = "Password123!"
    login = _create_and_login("doublesubmit1@mail.com", password)

    rt = login["refresh_token"]
    at = login["access_token"]

    # First logout (valid)
    r1 = client.post(
        "/auth/logout",
        json={"refresh_token": rt},
        headers={"Authorization": f"Bearer {at}"},
    )
    assert r1.status_code == 204

    # Second logout with same token (revoked) must fail
    r2 = client.post(
        "/auth/logout",
        json={"refresh_token": rt},
        headers={"Authorization": f"Bearer {at}"},
    )
    assert r2.status_code == 401


def test_refresh_with_revoked_token_after_logout() -> None:
    """Refresh token revoked by logout cannot be used for refresh."""
    password = "Password123!"
    login = _create_and_login("revoked1@mail.com", password)

    rt = login["refresh_token"]
    at = login["access_token"]

    # Logout
    client.post(
        "/auth/logout",
        json={"refresh_token": rt},
        headers={"Authorization": f"Bearer {at}"},
    )

    # Refresh must fail
    resp = client.post("/auth/refresh", json={"refresh_token": rt})
    assert resp.status_code == 401


def test_login_returns_valid_access_token_works_after_refresh() -> None:
    """Access token from login must remain valid even after refresh rotation."""
    password = "Password123!"
    login = _create_and_login("accesstest1@mail.com", password)

    at = login["access_token"]

    # Refresh (rotates refresh token)
    client.post(
        "/auth/refresh",
        json={"refresh_token": login["refresh_token"]},
    )

    # Old access token should still work (valid until expiry)
    me_resp = client.get(
        "/users/me",
        headers={"Authorization": f"Bearer {at}"},
    )
    assert me_resp.status_code == 200
