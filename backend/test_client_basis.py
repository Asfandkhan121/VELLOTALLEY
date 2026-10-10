"""Per-client accounting basis: endpoints (fake repo) + static migration checks."""
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.config import Settings
from app.main import create_app

AUTH = {"Authorization": "Bearer good"}
CID = "11111111-1111-1111-1111-111111111111"
SQL = (Path(__file__).parent / "database" / "0010_add_client_accounting_basis.sql").read_text()
CODE = "\n".join(l for l in SQL.splitlines() if not l.strip().startswith("--"))


class FakeRepository:
    def __init__(self, owns=True):
        self.owns, self.calls = owns, []

    def authenticate(self, token):
        if token != "good":
            raise RuntimeError("bad token")
        return "user-1"

    def client_belongs_to_user(self, client_id, user_id):
        return self.owns and user_id == "user-1"

    def get_client_basis(self, client_id, user_id):
        return {"accounting_basis": None, "basis_confirmed_at": None}

    def set_client_basis(self, client_id, user_id, basis):
        self.calls.append((str(client_id), user_id, basis))
        return {"accounting_basis": basis, "basis_confirmed_at": "t" if basis else None}


def _client(repo):
    return TestClient(create_app(Settings("https://example.supabase.co", "test-key"), repo))


def test_requires_authentication():
    c = _client(FakeRepository())
    assert c.get(f"/v1/clients/{CID}/basis").status_code == 401
    assert c.put(f"/v1/clients/{CID}/basis", json={"basis": "cash"}).status_code == 401


def test_default_is_unset():
    r = _client(FakeRepository()).get(f"/v1/clients/{CID}/basis", headers=AUTH)
    assert r.json() == {"accounting_basis": None, "basis_confirmed_at": None}


@pytest.mark.parametrize("value,stored", [("accrual", "accrual"), ("cash", "cash"), ("modified_cash", "modified_cash"), ("unset", None)])
def test_confirm_stores_choice_and_unset_clears(value, stored):
    repo = FakeRepository()
    r = _client(repo).put(f"/v1/clients/{CID}/basis", headers=AUTH, json={"basis": value})
    assert r.status_code == 200 and repo.calls == [(CID, "user-1", stored)]


def test_invalid_value_rejected_and_nothing_stored():
    repo = FakeRepository()
    c = _client(repo)
    for body in ({"basis": "maybe"}, {"basis": ""}, {}):
        assert c.put(f"/v1/clients/{CID}/basis", headers=AUTH, json=body).status_code == 422
    assert repo.calls == []


def test_non_owner_gets_404_and_nothing_stored():
    repo = FakeRepository(owns=False)
    c = _client(repo)
    assert c.put(f"/v1/clients/{CID}/basis", headers=AUTH, json={"basis": "cash"}).status_code == 404
    assert c.get(f"/v1/clients/{CID}/basis", headers=AUTH).status_code == 404
    assert repo.calls == []


def test_migration_unset_default_values_and_pairing():
    assert "in ('accrual', 'cash', 'modified_cash')" in CODE
    assert "default" not in CODE                      # unset (NULL) is the default
    assert "(accounting_basis is null) = (basis_confirmed_at is null)" in CODE
    assert "needs_review" not in CODE and "confidence" not in CODE
