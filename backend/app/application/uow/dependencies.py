"""Dependency functions for unit of work and database session management."""

from typing import Annotated

from fastapi import Depends
from sqlalchemy.orm import Session

from backend.app.application.uow.unit_of_work import UnitOfWork
from backend.app.infrastructure.db.dependencies import get_db


def get_uow(
    session: Annotated[Session, Depends(get_db)],
) -> UnitOfWork:
    uow = UnitOfWork(lambda: session)
    uow.attach(session)
    return uow
