"""Pydantic schemas for auth endpoints and token payloads."""

from pydantic import BaseModel, EmailStr


class LoginRequest(BaseModel):
    """Payload for login requests."""

    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    """Response returned after successful authentication."""

    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int | None = None


class RefreshTokenRequest(BaseModel):
    """Payload for refresh token exchange."""

    refresh_token: str
