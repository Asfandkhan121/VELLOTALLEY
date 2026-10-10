from fastapi.testclient import TestClient

from app.config import Settings
from app.main import create_app
from app.repository import SupabaseRepository


class FakeRepository:
    def authenticate(self, token):
        if token != "good":
            raise RuntimeError("bad token")
        return "user-1"

    def list_account_heads(self):
        return [{"id": "h1", "main_head": "Expenses", "sub_head": "Utilities"}]


def _client():
    return TestClient(create_app(Settings("https://example.supabase.co", "test-key"), FakeRepository()))


def test_account_heads_requires_authentication():
    assert _client().get("/v1/account-heads").status_code == 401
    assert _client().get("/v1/account-heads", headers={"Authorization": "Bearer bad"}).status_code == 401


def test_account_heads_returns_heads_for_authenticated_user():
    r = _client().get("/v1/account-heads", headers={"Authorization": "Bearer good"})
    assert r.status_code == 200
    assert r.json() == [{"id": "h1", "main_head": "Expenses", "sub_head": "Utilities"}]


def test_repository_orders_by_main_then_sub_head():
    calls = []

    class Q:
        def select(self, cols): calls.append(("select", cols)); return self
        def order(self, col): calls.append(("order", col)); return self
        def execute(self):
            class R: data = None
            return R()

    repo = SupabaseRepository.__new__(SupabaseRepository)
    repo.client = type("C", (), {"table": lambda self, n: (calls.append(("table", n)), Q())[1]})()
    assert repo.list_account_heads() == []
    assert calls == [("table", "account_heads"), ("select", "id,main_head,sub_head"), ("order", "main_head"), ("order", "sub_head")]
