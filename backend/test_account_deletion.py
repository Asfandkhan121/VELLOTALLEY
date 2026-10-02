from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.config import Settings
from app.main import create_app
from app.repository import SupabaseRepository


class FakeStorage:
    def __init__(self, events: list[tuple], *, fail_listing: bool = False):
        self.events = events
        self.fail_listing = fail_listing

    def list(self, path: str, options: dict) -> list[dict]:
        self.events.append(("list", path, options["offset"]))
        if self.fail_listing:
            raise RuntimeError("Storage listing failed")
        if path == "user-1":
            return [
                {"name": "loose.pdf", "id": "object-1"},
                {"name": "statement-1", "id": None},
            ]
        if path == "user-1/statement-1":
            offset = options["offset"]
            names = [f"source-{index}.pdf" for index in range(offset, min(offset + 1000, 1001))]
            return [{"name": name, "id": f"object-{offset + index}"} for index, name in enumerate(names)]
        return []

    def remove(self, paths: list[str]) -> list[dict]:
        self.events.append(("remove", paths))
        return []


class FakeQuery:
    def __init__(self, events: list[tuple], table: str):
        self.events = events
        self.table = table

    def delete(self):
        return self

    def eq(self, column: str, value: str):
        self.filter = (column, value)
        return self

    def execute(self):
        self.events.append(("delete_rows", self.table, self.filter))


class FakeAuthAdmin:
    def __init__(self, events: list[tuple]):
        self.events = events

    def delete_user(self, user_id: str, *, should_soft_delete: bool):
        self.events.append(("delete_auth_user", user_id, should_soft_delete))


class FakeStorageFactory:
    def __init__(self, storage: FakeStorage):
        self.storage = storage

    def from_(self, bucket: str) -> FakeStorage:
        assert bucket == "statements"
        return self.storage


class FakeClient:
    def __init__(self, *, fail_listing: bool = False):
        self.events: list[tuple] = []
        self.storage_api = FakeStorage(self.events, fail_listing=fail_listing)
        self.storage = FakeStorageFactory(self.storage_api)
        self.auth = type("Auth", (), {})()
        self.auth.admin = FakeAuthAdmin(self.events)

    def table(self, name: str):
        return FakeQuery(self.events, name)


def test_delete_account_removes_nested_storage_in_batches_before_user_data():
    client = FakeClient()
    repository = SupabaseRepository.__new__(SupabaseRepository)
    repository.client = client
    repository.bucket = "statements"

    repository.delete_account("user-1")

    removals = [event[1] for event in client.events if event[0] == "remove"]
    assert [len(batch) for batch in removals] == [1, 1000, 1]
    assert removals[0] == ["user-1/loose.pdf"]
    assert removals[1][0] == "user-1/statement-1/source-0.pdf"
    assert removals[2] == ["user-1/statement-1/source-1000.pdf"]
    assert [event[1] for event in client.events if event[0] == "delete_rows"] == [
        "demand_signals",
        "statement_notes",
        "clients",
    ]
    first_database_delete = next(index for index, event in enumerate(client.events) if event[0] == "delete_rows")
    last_storage_remove = max(index for index, event in enumerate(client.events) if event[0] == "remove")
    assert last_storage_remove < first_database_delete
    assert client.events[-1] == ("delete_auth_user", "user-1", False)


def test_delete_account_stops_before_database_and_auth_when_storage_listing_fails():
    client = FakeClient(fail_listing=True)
    repository = SupabaseRepository.__new__(SupabaseRepository)
    repository.client = client
    repository.bucket = "statements"

    with pytest.raises(RuntimeError, match="Storage listing failed"):
        repository.delete_account("user-1")

    assert not any(event[0] in {"delete_rows", "delete_auth_user"} for event in client.events)


def test_delete_account_endpoint_requires_authentication_and_returns_no_content():
    class FakeRepository:
        def __init__(self):
            self.deleted_users: list[str] = []

        def authenticate(self, access_token: str) -> str:
            assert access_token == "valid-token"
            return "user-1"

        def delete_account(self, user_id: str) -> None:
            self.deleted_users.append(user_id)

    repository = FakeRepository()
    app = create_app(Settings("https://example.supabase.co", "test-key"), repository)
    client = TestClient(app)

    unauthorized = client.delete("/v1/account")
    deleted = client.delete("/v1/account", headers={"Authorization": "Bearer valid-token"})

    assert unauthorized.status_code == 401
    assert deleted.status_code == 204
    assert deleted.content == b""
    assert repository.deleted_users == ["user-1"]


def test_delete_account_endpoint_reports_partial_failure():
    class FailingRepository:
        def authenticate(self, access_token: str) -> str:
            return "user-1"

        def delete_account(self, user_id: str) -> None:
            raise RuntimeError("provider-specific details must not be returned")

    app = create_app(Settings("https://example.supabase.co", "test-key"), FailingRepository())
    response = TestClient(app).delete(
        "/v1/account",
        headers={"Authorization": "Bearer valid-token"},
    )

    assert response.status_code == 502
    assert "Some data may already have been removed" in response.json()["detail"]
    assert "provider-specific details" not in response.text
