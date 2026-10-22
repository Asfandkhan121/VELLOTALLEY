"""Static checks on the client accounting-basis migration (no database needed)."""
from pathlib import Path

SQL = (Path(__file__).parent / "database" / "0010_add_client_accounting_basis.sql").read_text()
CODE = "\n".join(l for l in SQL.splitlines() if not l.strip().startswith("--"))


def test_adds_basis_column_on_clients_defaulting_to_unset():
    assert "alter table public.clients" in CODE
    assert "add column accounting_basis text not null default 'unset'" in CODE
    assert "create table" not in CODE


def test_allows_only_the_four_basis_values():
    assert "check (accounting_basis in ('accrual', 'cash', 'modified_cash', 'unset'))" in CODE


def test_does_not_guess_a_basis_or_touch_review_flags():
    assert "update " not in CODE.lower()
    assert "insert " not in CODE.lower()
    assert "needs_review" not in CODE and "confidence" not in CODE
