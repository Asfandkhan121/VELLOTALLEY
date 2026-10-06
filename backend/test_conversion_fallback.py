from datetime import datetime, timezone
from uuid import uuid4

from fastapi.testclient import TestClient
import app.main as main
from app.config import Settings
from app.main import _should_use_llm_fallback
from app.repository import SupabaseRepository, _TRANSACTION_LIST_PAGE_SIZE


def test_missing_balance_confidence_does_not_escalate_valid_heuristic_result():
    assert not _should_use_llm_fallback({
        "confidence": None,
        "column_detection_failed": False,
    })


def test_unlimited_user_ids_are_loaded_from_server_environment(monkeypatch):
    monkeypatch.setenv("SUPABASE_URL", "https://example.supabase.co")
    monkeypatch.setenv("SUPABASE_SERVICE_ROLE_KEY", "test-key")
    monkeypatch.setenv(
        "FREE_UNLIMITED_USER_IDS",
        " user-one,USER-TWO ,,",
    )

    settings = Settings.from_environment()

    assert settings.unlimited_conversion_user_ids == frozenset({"user-one", "user-two"})


def test_failed_column_detection_escalates_to_llm():
    assert _should_use_llm_fallback({
        "confidence": None,
        "column_detection_failed": True,
    })


def test_low_balance_confidence_escalates_to_llm():
    assert _should_use_llm_fallback({
        "confidence": 0.84,
        "column_detection_failed": False,
    })


def test_monthly_conversion_count_only_counts_completed_statements():
    calls = []

    class Query:
        def select(self, *args, **kwargs):
            calls.append(("select", args, kwargs))
            return self

        def eq(self, column, value):
            calls.append(("eq", column, value))
            return self

        def gte(self, column, value):
            calls.append(("gte", column, value))
            return self

        def execute(self):
            return type("Response", (), {"count": 2})()

    class TableClient:
        def table(self, name):
            assert name == "statements"
            return Query()

    repository = SupabaseRepository.__new__(SupabaseRepository)
    repository.client = TableClient()

    count = repository.monthly_conversion_count(
        "user-1",
        datetime(2026, 10, 1, tzinfo=timezone.utc),
    )

    assert count == 2
    assert ("eq", "status", "completed") in calls


def test_unlimited_user_bypasses_monthly_limit_but_other_users_remain_capped():
    exempt_user_id = "f5b99f3f-f3e2-42b5-98da-90f66b44ce9b"
    ordinary_user_id = "ordinary-user"
    client_id = uuid4()
    calls = []

    class FakeRepository:
        def authenticate(self, token):
            return {
                "exempt-token": exempt_user_id,
                "ordinary-token": ordinary_user_id,
            }[token]

        def client_belongs_to_user(self, requested_client, user_id):
            assert requested_client == client_id
            assert user_id in {exempt_user_id, ordinary_user_id}
            return True

        def monthly_conversion_count(self, user_id, _month_start):
            calls.append(("monthly_conversion_count", user_id))
            return 3

        def upload_pdf(self, user_id, _statement_id, content):
            calls.append(("upload_pdf", user_id, content))

        def create_statement(self, **kwargs):
            calls.append(("create_statement", kwargs["user_id"]))
            return {"id": str(kwargs["statement_id"]), "status": "processing"}

    settings = Settings(
        "https://example.supabase.co",
        "test-key",
        unlimited_conversion_user_ids=frozenset({exempt_user_id}),
    )
    client = TestClient(main.create_app(settings, FakeRepository()))

    exempt_response = client.post(
        "/v1/statements",
        headers={"Authorization": "Bearer exempt-token"},
        data={"client_id": str(client_id), "bank_profile": "auto"},
        files={"file": ("statement.pdf", b"%PDF-test", "application/pdf")},
    )
    assert exempt_response.status_code == 201
    assert ("monthly_conversion_count", exempt_user_id) not in calls

    ordinary_response = client.post(
        "/v1/statements",
        headers={"Authorization": "Bearer ordinary-token"},
        data={"client_id": str(client_id), "bank_profile": "auto"},
        files={"file": ("statement.pdf", b"%PDF-test", "application/pdf")},
    )
    assert ordinary_response.status_code == 429
    assert ("monthly_conversion_count", ordinary_user_id) in calls
    assert calls.count(("upload_pdf", exempt_user_id, b"%PDF-test")) == 1
    assert not any(call[:2] == ("upload_pdf", ordinary_user_id) for call in calls)


def test_get_transactions_fetches_all_pages_in_sequence_order():
    statement_id = uuid4()
    rows = [
        {
            "date": "2025-07-02",
            "description": f"transaction {sequence}",
            "debit": None,
            "credit": "1.00",
            "balance": str(sequence),
            "needs_review": True,
        }
        for sequence in range(1, _TRANSACTION_LIST_PAGE_SIZE * 2 + 57)
    ]
    ranges = []

    class Query:
        def __init__(self):
            self.start = 0
            self.end = 0

        def select(self, *_args, **_kwargs):
            return self

        def eq(self, column, value):
            assert column == "statement_id"
            assert value == str(statement_id)
            return self

        def order(self, column):
            assert column == "transaction_sequence"
            return self

        def range(self, start, end):
            ranges.append((start, end))
            self.start = start
            self.end = end
            return self

        def execute(self):
            return type("Response", (), {"data": rows[self.start:self.end + 1]})()

    class TableClient:
        def table(self, name):
            assert name == "transactions"
            return Query()

    repository = SupabaseRepository.__new__(SupabaseRepository)
    repository.client = TableClient()

    transactions = repository.get_transactions(statement_id)

    assert len(transactions) == len(rows)
    assert transactions[0]["description"] == "transaction 1"
    assert transactions[-1]["description"] == f"transaction {len(rows)}"
    assert ranges == [(0, 999), (1000, 1999), (2000, 2999)]


def test_empty_profile_parse_marks_statement_failed(monkeypatch):
    statement_id = uuid4()

    class FakeRepository:
        def __init__(self):
            self.statuses = []

        def authenticate(self, token):
            assert token == "local-test-token"
            return "user-1"

        def get_statement(self, requested_id, user_id):
            assert requested_id == statement_id
            assert user_id == "user-1"
            return {"id": str(statement_id), "status": "processing", "bank_profile": "test-profile"}

        def download_pdf(self, user_id, requested_id):
            return b"%PDF-test"

        def set_statement_status(self, requested_id, user_id, status, **kwargs):
            self.statuses.append(status)

    repository = FakeRepository()
    monkeypatch.setattr(main, "BANK_PROFILES", {"test-profile": {}})
    monkeypatch.setattr(main, "parse_statement", lambda *_args: [])
    client = TestClient(main.create_app(Settings("https://example.supabase.co", "test-key"), repository))

    response = client.post(
        f"/v1/statements/{statement_id}/extract",
        headers={"Authorization": "Bearer local-test-token"},
    )

    assert response.status_code == 422
    assert "No transactions" in response.json()["detail"]
    assert repository.statuses == ["failed"]
