"""User repository for managing user data."""

from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.app.modules.user.domain.models import User


class UserRepository:
    def __init__(self, session: Session):
        self.session = session

    def create(self, user: User) -> User:
        self.session.add(user)
        self.session.flush()

        return user

    def get_by_id(self, user_id: int) -> User | None:
        statement = select(User).where(User.id == user_id)

        result = self.session.execute(statement)
        return result.scalar_one_or_none()

    def get_by_email(self, email: str) -> User | None:
        statement = select(User).where(User.email == email)

        result = self.session.execute(statement)
        return result.scalar_one_or_none()

    def list(self, limit: int = 20, offset: int = 0) -> list[User]:
        statement = select(User).order_by(User.id).limit(limit).offset(offset)

        result = self.session.execute(statement)
        return list(result.scalars().all())

    def update(self, user: User) -> User:
        self.session.add(user)
        self.session.flush()

        return user

    def delete(self, user: User) -> None:
        self.session.delete(user)
        self.session.flush()
