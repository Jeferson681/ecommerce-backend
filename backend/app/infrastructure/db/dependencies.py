from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from backend.app.core.config import settings

# SQLite requires check_same_thread=False for multi-threaded access; other
# drivers (e.g. PostgreSQL) reject it as an unknown connection option.
connect_args = (
    {"check_same_thread": False} if settings.DATABASE_URL.startswith("sqlite") else {}
)

engine = create_engine(
    settings.DATABASE_URL,
    echo=False,
    connect_args=connect_args,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db() -> Generator[Session]:
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()
