"""Unit tests for intl_parsing.py.

All fixtures below are SYNTHETIC -- hand-written strings shaped like the
patterns described in the ticket, not extracted from any real bank PDF (none
were available for HBL, UBL's international products, Emirates NBD, ADCB,
Al Rajhi, or NCB). They prove the helper functions behave correctly on
well-formed input matching the spec; they do NOT prove any real bank's
statement will parse correctly, since no bank-specific layout code exists
yet (see intl_parsing.py's module docstring for why).
"""
from decimal import Decimal

from intl_parsing import (
    detect_country_from_iban,
    extract_iban,
    normalize_date,
    merge_fx_lines,
    validate_running_balance,
)


def test_iban_detection_pk():
    assert detect_country_from_iban("IBAN No: PK26 UNIL 0112 0104 1000 9325") == "PK"


def test_iban_detection_ae():
    assert detect_country_from_iban("Account IBAN AE070331234567890123456") == "AE"


def test_iban_detection_sa():
    assert detect_country_from_iban("SA0380000000608010167519") == "SA"


def test_iban_detection_none():
    assert detect_country_from_iban("Account Number 010410009325") is None


def test_extract_iban_strips_spaces():
    assert extract_iban("IBAN: PK26 UNIL 0112 0104 1000 9325") == "PK26UNIL0112010410009325"


def test_extract_iban_does_not_swallow_trailing_label():
    # Regression test: a real UBL statement line has "...9325 CIF#: 21663136"
    # right after the IBAN. The ticket's literal open-ended regex captured
    # "CIF" as part of the IBAN in manual testing; the fixed-length pattern
    # must stop exactly at the real IBAN boundary.
    real_line = "IBAN No: PK26 UNIL 0112 0104 1000 9325 CIF#: 21663136"
    assert extract_iban(real_line) == "PK26UNIL0112010410009325"
    assert detect_country_from_iban(real_line) == "PK"


def test_normalize_date_ddmmyyyy_slash():
    result = normalize_date("05/12/2025")
    assert result["iso_date"] == "2025-12-05"
    assert result["is_hijri"] is False


def test_normalize_date_ddmmyyyy_dash():
    result = normalize_date("05-12-2025")
    assert result["iso_date"] == "2025-12-05"


def test_normalize_date_ddmmmyyyy():
    result = normalize_date("05-Dec-2025")
    assert result["iso_date"] == "2025-12-05"


def test_normalize_date_hijri_detected_not_converted():
    result = normalize_date("1447/06/12")
    assert result["is_hijri"] is True
    assert result["iso_date"] is None  # detection only -- see docstring


def test_normalize_date_unparseable_returns_none():
    result = normalize_date("REF-99182736")
    assert result["iso_date"] is None
    assert result["is_hijri"] is False


def test_normalize_date_fallback_extracts_embedded_date():
    result = normalize_date("Value Date 12/06/2025 Ref XYZ")
    assert result["iso_date"] == "2025-06-12"


def test_merge_fx_lines_basic():
    lines = [
        "POS Purchase Amazon.com",
        "USD 49.99",
        "PKR 13,972.20",
        "Card fee PKR 350.00",
    ]
    merged = merge_fx_lines(lines, local_currency="PKR")
    assert merged is not None
    assert merged["foreign_amount"] == 49.99
    assert merged["foreign_currency"] == "USD"
    assert merged["local_amount"] == 13972.20
    assert merged["fee"] == 350.00
    assert merged["local_currency"] == "PKR"


def test_merge_fx_lines_no_fee():
    lines = ["Card Purchase", "EUR 120.00", "PKR 36,500.00"]
    merged = merge_fx_lines(lines, local_currency="PKR")
    assert merged["foreign_currency"] == "EUR"
    assert merged["fee"] is None


def test_merge_fx_lines_returns_none_when_no_foreign_currency():
    lines = ["Cheque Withdrawal", "PKR 26,000.00"]
    assert merge_fx_lines(lines, local_currency="PKR") is None


def test_validate_running_balance_all_within_tolerance():
    txns = [
        {"debit": None, "credit": 100.0, "balance": 1100.0},
        {"debit": 50.0, "credit": None, "balance": 1050.0},
    ]
    results = validate_running_balance(txns, opening_balance=1000.0, tolerance_pct=0.5)
    assert all(not r["flagged"] for r in results)


def test_validate_running_balance_flags_large_mismatch():
    txns = [
        {"debit": None, "credit": 100.0, "balance": 5000.0},  # way off vs expected 1100.0
    ]
    results = validate_running_balance(txns, opening_balance=1000.0, tolerance_pct=0.5)
    assert results[0]["flagged"] is True
    assert results[0]["balance_diff_pct"] > 0.5


def test_validate_running_balance_within_half_percent_not_flagged():
    # expected 100000.0, printed 100400.0 -> 0.4% off, should pass at 0.5% tolerance
    txns = [{"debit": None, "credit": 0.0, "balance": 100400.0}]
    results = validate_running_balance(txns, opening_balance=100000.0, tolerance_pct=0.5)
    assert results[0]["flagged"] is False


if __name__ == "__main__":
    import sys
    import types

    tests = [(name, obj) for name, obj in list(globals().items()) if name.startswith("test_")]
    failures = 0
    for name, fn in tests:
        try:
            fn()
            print(f"PASS  {name}")
        except AssertionError as exc:
            failures += 1
            print(f"FAIL  {name}: {exc}")
        except Exception as exc:  # pragma: no cover
            failures += 1
            print(f"ERROR {name}: {exc!r}")
    print(f"\n{len(tests) - failures}/{len(tests)} passed")
    sys.exit(1 if failures else 0)
