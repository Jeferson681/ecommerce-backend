from collections.abc import Generator
from typing import Annotated

from fastapi import Depends
from sqlalchemy.orm import Session

from app.application.uow.unit_of_work import UnitOfWork
from app.core.database import SessionLocal


def get_db() -> Generator[Session, None, None]:
    session = SessionLocal()

    try:
        yield session

    finally:
        session.close()


def get_uow(
    session: Annotated[Session, Depends(get_db)],
) -> UnitOfWork:
    return UnitOfWork(session)
