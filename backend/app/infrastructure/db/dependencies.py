from collections.abc import Generator

from sqlalchemy.orm import Session

from backend.app.core.database import SessionLocal


def get_db() -> Generator[Session]:
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()
