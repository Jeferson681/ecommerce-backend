import pytest

from backend.app.core.exceptions import NotFoundError
from backend.app.modules.cart import use_cases


class RepoNone:
    def __init__(self, session):
        self.session = session

    def get_by_user_id(self, user_id: int):
        return None


def test_remove_item_raises_if_cart_missing(monkeypatch):
    # simulate missing cart
    monkeypatch.setattr(use_cases, "CartRepository", RepoNone)

    class DummyUoW:
        def __init__(self):
            self.session = object()
            self.committed = False
            self.rolled_back = False

    uow = DummyUoW()

    with pytest.raises(NotFoundError):
        use_cases.remove_item(1, user_id=5, uow=uow)
