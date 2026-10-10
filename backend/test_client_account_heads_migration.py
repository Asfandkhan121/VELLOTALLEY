"""Static checks on the client_account_heads migration (no database needed).
Behaviour was also run against a real local Postgres; see the PR description."""
from pathlib import Path

SQL = (Path(__file__).parent / "database" / "0009_add_client_account_heads.sql").read_text()
CODE = "\n".join(l for l in SQL.splitlines() if not l.strip().startswith("--"))


def test_rls_enabled_with_owner_only_policy():
    assert "enable row level security" in CODE
    assert "auth.uid() = user_id" in CODE and CODE.count("create policy") == 1


def test_cascade_from_client_and_unique_name_per_client():
    assert "references public.clients(id) on delete cascade" in CODE
    assert "create unique index" in CODE and "(client_id, lower(" in CODE


def test_main_head_is_free_text_and_source_is_limited():
    assert "section text check (section is null" in CODE      # no fixed list of main heads
    assert "in ('trial_balance', 'cash_book', 'manual')" in CODE


def test_does_not_touch_review_or_confidence_columns():
    assert "needs_review" not in CODE and "confidence" not in CODE
