from sqlalchemy.orm import Session


class UnitOfWork:
    """Unit of Work pattern for managing database transactions."""

    def __init__(self, session: Session) -> None:
        self.session = session

    def commit(self) -> None:
        self.session.commit()

    def rollback(self) -> None:
        self.session.rollback()
