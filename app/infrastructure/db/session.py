"""Database session management."""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.database import DATABASE_URL

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db_session():
    return SessionLocal()
