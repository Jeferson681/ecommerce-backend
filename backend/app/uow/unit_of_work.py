import logging
from collections.abc import Callable
from typing import Any, Self

from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)


class UnitOfWork:
    """Encapsulates a SQLAlchemy Session with transactional control.

    Receives a Session factory and uses it to obtain a Session on entry.
    Provides commit, rollback and flush operations. Does NOT own the Session
    lifecycle — the Session must be closed by its creator (get_db).
    """

    def __init__(
        self,
        session_factory: Callable[[], Session],
    ) -> None:
        self.session_factory = session_factory
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
        self.attach(self.session_factory())
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
        self._session = None

    def commit(self) -> None:
        self.session.commit()

    def rollback(self) -> None:
        if self._session is not None:
            self._session.rollback()

    def flush(self) -> None:
        self.session.flush()
