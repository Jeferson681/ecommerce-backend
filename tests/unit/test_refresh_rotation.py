"""Comprehensive tests for Refresh Token Rotation (Phase 3).

Covers:
- login: persists refresh token record
- refresh: revokes old token + creates new one (rotation)
- replay: reusing a rotated token fails
- logout: revokes token
- token revogado: using a revoked token fails
"""

from __future__ import annotations

import os

import pytest

os.environ.setdefault("JWT_SECRET_KEY", "test-jwt-secret-for-unit-tests")

from backend.app.core.config import Settings
from backend.app.core.database import Base, engine
from backend.app.modules.auth import tokens as token_module, use_cases as auth_use_cases
from backend.app.modules.auth.repositories.refresh_token_repository import (
    RefreshTokenRepository,
)
from backend.app.modules.auth.tokens import jti_hash
from backend.app.modules.user.domain.models import User

_test_settings = Settings(
    JWT_SECRET_KEY="test-jwt-secret",
    JWT_ISSUER="test-issuer",
    JWT_AUDIENCE="test-audience",
)


@pytest.fixture(scope="module", autouse=True)
def db_setup():
    import backend.app.modules.cart.domain.models  # noqa: F401
    import backend.app.modules.order.domain.models  # noqa: F401
    import backend.app.modules.payment.domain.models  # noqa: F401
    import backend.app.modules.product.domain.models  # noqa: F401

    Base.metadata.create_all(bind=engine)
    try:
        yield
    finally:
        Base.metadata.drop_all(bind=engine)


@pytest.fixture(autouse=True)
def _patch_settings(monkeypatch):
    monkeypatch.setattr(
        token_module.settings, "JWT_SECRET_KEY", _test_settings.JWT_SECRET_KEY
    )
    monkeypatch.setattr(token_module.settings, "JWT_ISSUER", _test_settings.JWT_ISSUER)
    monkeypatch.setattr(
        token_module.settings, "JWT_AUDIENCE", _test_settings.JWT_AUDIENCE
    )
    import backend.app.core.config as cfg

    monkeypatch.setattr(cfg.settings, "JWT_SECRET_KEY", _test_settings.JWT_SECRET_KEY)
    monkeypatch.setattr(cfg.settings, "JWT_ISSUER", _test_settings.JWT_ISSUER)
    monkeypatch.setattr(cfg.settings, "JWT_AUDIENCE", _test_settings.JWT_AUDIENCE)


@pytest.fixture(autouse=True)
def _clean_tokens():
    from sqlalchemy import text

    with engine.connect() as conn:
        conn.execute(text("DELETE FROM refresh_tokens"))
        conn.commit()


class FakeUoW:
    def __init__(self):
        from sqlalchemy.orm import sessionmaker

        SessionFactory = sessionmaker(bind=engine, future=True)
        self.session = SessionFactory()
        self.committed = False

    def commit(self):
        self.session.flush()
        self.committed = True

    def rollback(self):
        self.session.rollback()

    def close(self):
        self.session.close()


def _create_user(session):
    user = User(
        first_name="Refresh",
        last_name="Test",
        email="refresh@test.com",
        password_hash="hashed:password",
    )
    session.add(user)
    session.flush()
    session.refresh(user)
    return user


def _mock_login(monkeypatch, user):
    monkeypatch.setattr(auth_use_cases, "verify_password", lambda plain, hashed: True)

    class FakeUserRepo:
        def __init__(self, session):
            self.session = session

        def get_by_email(self, email):
            return user

    monkeypatch.setattr(auth_use_cases, "UserRepository", FakeUserRepo)


class TestLogin:
    def test_login_persists_refresh_token(self, monkeypatch):
        uow = FakeUoW()
        user = _create_user(uow.session)
        uow.commit()
        _mock_login(monkeypatch, user)
        response = auth_use_cases.login(email=user.email, password="any", uow=uow)
        repo = RefreshTokenRepository(uow.session)
        payload = token_module.decode_refresh_token(response.refresh_token)
        record = repo.get_by_jti_hash(jti_hash(payload["jti"]))
        assert record is not None
        assert record.user_id == user.id
        assert record.revoked is False
        assert record.jti_hash == jti_hash(payload["jti"])
        assert record.expires_at is not None
        uow.close()

    def test_login_returns_valid_tokens(self, monkeypatch):
        uow = FakeUoW()
        user = _create_user(uow.session)
        uow.commit()
        _mock_login(monkeypatch, user)
        response = auth_use_cases.login(email=user.email, password="any", uow=uow)
        access_payload = token_module.decode_access_token(response.access_token)
        assert access_payload["sub"] == str(user.id)
        refresh_payload = token_module.decode_refresh_token(response.refresh_token)
        assert refresh_payload["sub"] == str(user.id)
        assert refresh_payload["type"] == "refresh"
        uow.close()


class TestRefresh:
    def test_refresh_rotates_token(self, monkeypatch):
        uow = FakeUoW()
        user = _create_user(uow.session)
        uow.commit()
        _mock_login(monkeypatch, user)
        login_response = auth_use_cases.login(email=user.email, password="any", uow=uow)
        old_refresh = login_response.refresh_token
        old_payload = token_module.decode_refresh_token(old_refresh)
        old_jti_hash_val = jti_hash(old_payload["jti"])
        refresh_response = auth_use_cases.refresh_access_token(old_refresh, uow)
        repo = RefreshTokenRepository(uow.session)
        old_record = repo.get_by_jti_hash(old_jti_hash_val)
        assert old_record is not None
        assert old_record.revoked is True
        assert refresh_response.refresh_token != old_refresh
        new_payload = token_module.decode_refresh_token(refresh_response.refresh_token)
        new_record = repo.get_by_jti_hash(jti_hash(new_payload["jti"]))
        assert new_record is not None
        assert new_record.revoked is False
        uow.close()

    def test_refresh_with_revoked_token_fails(self, monkeypatch):
        uow = FakeUoW()
        user = _create_user(uow.session)
        uow.commit()
        _mock_login(monkeypatch, user)
        login_response = auth_use_cases.login(email=user.email, password="any", uow=uow)
        old_refresh = login_response.refresh_token
        auth_use_cases.refresh_access_token(old_refresh, uow)
        with pytest.raises(Exception, match="Invalid email or password"):
            auth_use_cases.refresh_access_token(old_refresh, uow)
        uow.close()


class TestLogout:
    def test_logout_revokes_token(self, monkeypatch):
        uow = FakeUoW()
        user = _create_user(uow.session)
        uow.commit()
        _mock_login(monkeypatch, user)
        login_response = auth_use_cases.login(email=user.email, password="any", uow=uow)
        refresh_token = login_response.refresh_token
        payload = token_module.decode_refresh_token(refresh_token)
        jti = jti_hash(payload["jti"])
        auth_use_cases.logout(refresh_token, uow)
        repo = RefreshTokenRepository(uow.session)
        record = repo.get_by_jti_hash(jti)
        assert record is not None
        assert record.revoked is True
        uow.close()

    def test_logout_with_revoked_token_fails(self, monkeypatch):
        uow = FakeUoW()
        user = _create_user(uow.session)
        uow.commit()
        _mock_login(monkeypatch, user)
        login_response = auth_use_cases.login(email=user.email, password="any", uow=uow)
        refresh_token = login_response.refresh_token
        auth_use_cases.logout(refresh_token, uow)
        with pytest.raises(Exception, match="Invalid email or password"):
            auth_use_cases.logout(refresh_token, uow)
        uow.close()

    def test_logout_with_invalid_token_fails(self):
        uow = FakeUoW()
        with pytest.raises(Exception, match="Invalid email or password"):
            auth_use_cases.logout("invalid_token_here", uow)
        uow.close()


class TestRevokedToken:
    def test_refresh_after_logout_fails(self, monkeypatch):
        uow = FakeUoW()
        user = _create_user(uow.session)
        uow.commit()
        _mock_login(monkeypatch, user)
        login_response = auth_use_cases.login(email=user.email, password="any", uow=uow)
        refresh_token = login_response.refresh_token
        auth_use_cases.logout(refresh_token, uow)
        with pytest.raises(Exception, match="Invalid email or password"):
            auth_use_cases.refresh_access_token(refresh_token, uow)
        uow.close()
