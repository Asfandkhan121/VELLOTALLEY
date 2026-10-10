import io

from fastapi.testclient import TestClient
from openpyxl import Workbook

from app.config import Settings
from app.main import create_app
from app.repository import SupabaseRepository

AUTH = {"Authorization": "Bearer good"}
CID = "11111111-1111-1111-1111-111111111111"


class FakeRepository:
    def __init__(self, owns=True, existing=()):
        self.owns, self.stored, self.existing = owns, [], list(existing)

    def authenticate(self, token):
        if token != "good":
            raise RuntimeError("bad token")
        return "user-1"

    def client_belongs_to_user(self, client_id, user_id):
        return self.owns and user_id == "user-1"

    def list_client_heads(self, client_id, user_id):
        return [{"name": n} for n in self.existing]

    def add_client_heads(self, client_id, user_id, source, heads):
        self.stored.append((str(client_id), user_id, source, heads))
        return heads


def _client(repo):
    return TestClient(create_app(Settings("https://example.supabase.co", "test-key"), repo))


def _xlsx():
    wb = Workbook()
    ws = wb.active
    for row in [["Acme LLC\nTrial Balance\nBasis: Accrual\nFrom 01 Jan 2025 To 31 Dec 2025"],
                ["Account ", "Net Debit ", "Net Credit "], [],
                ["Assets", ""], ["    Accounts Receivable", 100, 0], ["Liabilities", ""], ["    Accrued Salaries", 0, 30]]:
        ws.append(row)
    buf = io.BytesIO()
    wb.save(buf)
    return buf.getvalue()


def _upload(client, content, name="tb.xlsx"):
    return client.post(f"/v1/clients/{CID}/heads/proposals", headers=AUTH, files={"file": (name, content)})


def test_all_three_endpoints_require_authentication():
    c = _client(FakeRepository())
    assert c.get(f"/v1/clients/{CID}/heads").status_code == 401
    assert c.post(f"/v1/clients/{CID}/heads", json={}).status_code == 401
    assert c.post(f"/v1/clients/{CID}/heads/proposals", files={"file": ("a.xlsx", b"PK")}).status_code == 401


def test_someone_elses_client_is_404_and_nothing_is_stored_or_read():
    repo = FakeRepository(owns=False)
    c = _client(repo)
    assert c.get(f"/v1/clients/{CID}/heads", headers=AUTH).status_code == 404
    assert _upload(c, _xlsx()).status_code == 404
    r = c.post(f"/v1/clients/{CID}/heads", headers=AUTH, json={"source": "manual", "heads": [{"name": "Cash"}]})
    assert r.status_code == 404 and repo.stored == []


def test_proposals_return_heads_and_evidence_and_store_nothing():
    repo = FakeRepository()
    r = _upload(_client(repo), _xlsx())
    assert r.status_code == 200
    sheet = r.json()[0]
    assert sheet["stated_basis"] == "accrual" and sheet["hierarchy"] == "sections"
    assert [(h["name"], h["section"]) for h in sheet["heads"]] == [("Accounts Receivable", "Assets"), ("Accrued Salaries", "Liabilities")]
    assert set(sheet["evidence"]) == {"receivables", "accruals"}
    assert "values" not in sheet["heads"][0] and repo.stored == []


def test_proposal_upload_validation():
    c = _client(FakeRepository())
    assert _upload(c, _xlsx(), "tb.pdf").status_code == 415
    assert _upload(c, b"not a zip", "tb.xlsx").status_code == 415
    assert _upload(c, b"PK" + b"garbage", "tb.xlsx").status_code == 422
    assert _upload(c, b"PK" + b"0" * (10 * 1024 * 1024 + 1), "tb.xlsx").status_code == 413


def test_confirm_stores_with_user_id_from_token_not_body_and_skips_duplicates():
    repo = FakeRepository(existing=["Cash"])
    body = {"source": "trial_balance", "user_id": "attacker",
            "heads": [{"name": " Sundry  Debtors ", "section": "Assets"}, {"name": "sundry debtors"}, {"name": "CASH"}, {"name": "Rent", "section": "  "}]}
    r = _client(repo).post(f"/v1/clients/{CID}/heads", headers=AUTH, json=body)
    assert r.status_code == 201 and r.json() == {"created": 2, "skipped_existing": ["sundry debtors", "CASH"]}
    cid, uid, source, heads = repo.stored[0]
    assert (cid, uid, source) == (CID, "user-1", "trial_balance")
    assert [(h["name"], h["section"]) for h in heads] == [("Sundry  Debtors", "Assets"), ("Rent", None)]


def test_confirm_rejects_bad_input():
    c = _client(FakeRepository())
    url = f"/v1/clients/{CID}/heads"
    assert c.post(url, headers=AUTH, json={"source": "guess", "heads": [{"name": "A"}]}).status_code == 422
    assert c.post(url, headers=AUTH, json={"source": "manual", "heads": []}).status_code == 422
    assert c.post(url, headers=AUTH, json={"source": "manual", "heads": [{"name": "   "}]}).status_code == 422


def test_repository_filters_by_client_and_user_and_sets_owner():
    calls = []

    class Q:
        def __getattr__(self, name):
            def rec(*a):
                calls.append((name, *a))
                return self
            return rec

        def execute(self):
            class R:
                data = [{"id": "x"}]
            return R()

    repo = SupabaseRepository.__new__(SupabaseRepository)
    repo.client = type("C", (), {"table": lambda self, n: (calls.append(("table", n)), Q())[1]})()
    assert repo.list_client_heads(CID, "user-1") == [{"id": "x"}]
    assert ("eq", "client_id", CID) in calls and ("eq", "user_id", "user-1") in calls
    calls.clear()
    repo.add_client_heads(CID, "user-1", "manual", [{"name": "Cash"}])
    insert = next(c for c in calls if c[0] == "insert")
    assert insert[1] == [{"client_id": CID, "user_id": "user-1", "source": "manual", "name": "Cash", "section": None, "code": None}]
