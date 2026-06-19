from datetime import datetime

from sqlalchemy import select, update
from sqlalchemy.orm import Session

from backend.app.modules.auth.domain.models import RefreshToken


class RefreshTokenRepository:
    def __init__(self, session: Session):
        self.session = session

    def create(self, token: RefreshToken) -> RefreshToken:
        self.session.add(token)
        self.session.flush()
        return token

    def get_by_jti_hash(self, jti_hash: str) -> RefreshToken | None:
        stmt = select(RefreshToken).where(RefreshToken.jti_hash == jti_hash)
        result = self.session.execute(stmt)
        return result.scalar_one_or_none()

    def revoke(self, token_id: int) -> None:
        stmt = (
            update(RefreshToken).where(RefreshToken.id == token_id).values(revoked=True)
        )
        self.session.execute(stmt)
        self.session.flush()

    def update_last_used(self, token_id: int, when: datetime) -> None:
        stmt = (
            update(RefreshToken)
            .where(RefreshToken.id == token_id)
            .values(last_used_at=when)
        )
        self.session.execute(stmt)
        self.session.flush()
