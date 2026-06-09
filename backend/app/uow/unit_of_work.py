import logging
from abc import ABC, abstractmethod
from collections.abc import Callable
from typing import Any, Self

from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)


class BaseUnitOfWork(ABC):
    def __init__(self) -> None:
        self._session: Session | None = None

    def attach(self, session: Session) -> None:
        """Attach an active SQLAlchemy Session to this UoW instance."""
        self._session = session

    @property
    def session(self) -> Session:
        """Return the active Session or raise if not initialized."""
        if self._session is None:
            raise RuntimeError("Session is not initialized.")

        return self._session

    def __enter__(self) -> Self:
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: Any,
    ) -> None:
        if exc_type is not None:
            try:
                self.rollback()
            except Exception:
                logger.exception("Rollback failed")

    @abstractmethod
    def commit(self) -> None:
        raise NotImplementedError

    @abstractmethod
    def rollback(self) -> None:
        raise NotImplementedError

    @abstractmethod
    def flush(self) -> None:
        raise NotImplementedError


class UnitOfWork(BaseUnitOfWork):
    def __init__(
        self,
        session_factory: Callable[[], Session],
    ) -> None:
        super().__init__()
        self.session_factory = session_factory

    def __enter__(self) -> Self:
        self.attach(self.session_factory())
        return super().__enter__()

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: Any,
    ) -> None:
        try:
            super().__exit__(
                exc_type,
                exc_val,
                exc_tb,
            )
        finally:
            if self._session is not None:
                self._session.close()
                self._session = None

    def commit(self) -> None:
        self.session.commit()

    def rollback(self) -> None:
        if self._session is not None and self._session.is_active:
            self._session.rollback()

    def flush(self) -> None:
        self.session.flush()
