from collections.abc import Generator
from typing import Annotated

from fastapi import Depends
from sqlalchemy.orm import Session

from backend.app.infrastructure.db.dependencies import get_db
from backend.app.uow.unit_of_work import UnitOfWork


def get_uow(
    session: Annotated[Session, Depends(get_db)],
) -> Generator[UnitOfWork, None, None]:
    with UnitOfWork(lambda: session) as uow:
        yield uow
