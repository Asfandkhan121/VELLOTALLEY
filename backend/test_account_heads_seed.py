"""Static consistency checks for the account-heads migration and the proposed
seed. No database needed; a real-Postgres run is documented in the PR."""
import re
from pathlib import Path

DB = Path(__file__).parent / "database"
MIG = (DB / "0008_add_account_heads.sql").read_text()
SEED = (DB / "proposed" / "account_heads_seed.sql").read_text()
MAINS = set(re.search(r"main_head in \((.*?)\)\)", MIG, re.S).group(1).replace("'", "").replace("\n", "").split(","))
MAINS = {m.strip() for m in MAINS}
STR = r"'((?:[^']|'')*)'"


def _heads():
    block = SEED.split("insert into public.account_head_aliases")[0]
    return re.findall(rf"\({STR}, {STR}\)", block)


def _aliases():
    block = SEED.split("from (values")[1].split(") as v(")[0]
    return re.findall(rf"\({STR}, {STR}, {STR}, {STR}\)", block)


def test_heads_use_allowed_main_heads_and_are_unique():
    heads = _heads()
    assert heads and {m for m, _ in heads} <= MAINS
    assert len(heads) == len(set(heads))


def test_aliases_are_normalized_unique_and_point_to_real_heads():
    heads, aliases = set(_heads()), _aliases()
    assert aliases
    keys = [(a, b) for a, b, _, _ in aliases]
    assert len(keys) == len(set(keys))
    for a, b, m, s in aliases:
        assert (m, s) in heads
        for x in (a, b):
            assert x == re.sub(r"\s+", " ", x.strip().lower())


def test_bank_side_rows_are_not_heads():
    assert not any(s.lower() in {"cash at bank", "bank account"} for _, s in _heads())
