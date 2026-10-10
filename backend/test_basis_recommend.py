import itertools

import pytest
from fastapi.testclient import TestClient

from app.config import Settings
from app.main import create_app
from basis_recommend import QUESTIONS, InvalidAnswers, recommend
from test_client_basis import AUTH, CID, FakeRepository

IDS = [q["id"] for q in QUESTIONS]


def ans(inc, exp, ast, pay):
    return dict(zip(IDS, [inc, exp, ast, pay]))


@pytest.mark.parametrize("a,expected", [
    (ans("accrual", "accrual", "tracked", "tracked"), "accrual"),
    (ans("accrual", "accrual", "cash", "cash"), "accrual"),
    (ans("cash", "cash", "cash", "cash"), "cash"),
    (ans("cash", "cash", "tracked", "cash"), "modified_cash"),
    (ans("cash", "cash", "cash", "tracked"), "modified_cash"),
    (ans("accrual", "cash", "cash", "cash"), None),       # conflict
    (ans("cash", "accrual", "tracked", "tracked"), None),  # conflict
])
def test_rule(a, expected):
    assert recommend(a)["recommendation"] == expected


def test_any_not_sure_gives_no_recommendation():
    for i, q in enumerate(QUESTIONS):
        a = ans("accrual", "accrual", "tracked", "tracked")
        a[q["id"]] = "unsure"
        assert recommend(a)["recommendation"] is None


def test_every_combination_is_handled_and_only_known_bases():
    ok = {None, "accrual", "cash", "modified_cash"}
    for combo in itertools.product(*[[o["id"] for o in q["options"]] for q in QUESTIONS]):
        assert recommend(dict(zip(IDS, combo)))["recommendation"] in ok


def test_bad_answers_rejected():
    for a in ({}, ans("accrual", "accrual", "tracked", "bogus"), {**ans("cash", "cash", "cash", "cash"), "extra": "x"}):
        with pytest.raises(InvalidAnswers):
            recommend(a)


def _c():
    return TestClient(create_app(Settings("https://example.supabase.co", "test-key"), FakeRepository()))


def test_endpoints_auth_ownership_and_nothing_stored():
    c = _c()
    assert c.get("/v1/basis/questions").status_code == 401
    assert c.post(f"/v1/clients/{CID}/basis/recommendation", json={"answers": {}}).status_code == 401
    assert len(c.get("/v1/basis/questions", headers=AUTH).json()) == 4
    r = c.post(f"/v1/clients/{CID}/basis/recommendation", headers=AUTH, json={"answers": ans("cash", "cash", "cash", "cash")})
    assert r.json()["recommendation"] == "cash"
    assert c.post(f"/v1/clients/{CID}/basis/recommendation", headers=AUTH, json={"answers": {}}).status_code == 422
    repo = FakeRepository(owns=False)
    c2 = TestClient(create_app(Settings("https://example.supabase.co", "test-key"), repo))
    assert c2.post(f"/v1/clients/{CID}/basis/recommendation", headers=AUTH, json={"answers": ans("cash", "cash", "cash", "cash")}).status_code == 404
    assert repo.calls == []
