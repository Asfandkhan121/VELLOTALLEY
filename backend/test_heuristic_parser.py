from heuristic_parser import (
    _amount_direction,
    _amount_columns,
    _associate_nearby_balances,
    _column_bounds,
    _detect_day_first,
    _detect_header_columns,
    _parse_date_any,
    _transaction_date,
    _uses_grouped_primary_dates,
)
from statement_converter import _amount, _text


def word(text, x0, x1, top=100.0):
    return {"text": text, "x0": x0, "x1": x1, "top": top, "bottom": top + 8}


def test_header_mapping_uses_named_columns_and_keeps_value_date_separate():
    header = [
        word("DATE", 45, 74),
        word("PARTICULARS", 87, 159),
        word("INS", 329, 342),
        word("#/Time", 344, 368),
        word("VAL", 385, 400),
        word("DATE", 403, 424),
        word("AMOUNT", 466, 508),
        word("BALANCE", 553, 599),
    ]
    columns = _detect_header_columns([header], 612)

    assert columns is not None
    bounds = columns["bounds"]
    assert set(bounds) == {"date", "description", "value_date", "amount", "balance"}
    assert bounds["date"][1] < bounds["description"][1]
    assert bounds["description"][1] < bounds["value_date"][0]

    row = [
        word("03/10/2025", 42, 79, 200),
        word("SCHOOL", 87, 150, 200),
        word("386", 148, 162, 200),
        word("03/10/2025", 386, 424, 200),
        word("1,250.00", 476, 508, 200),
    ]
    assert _parse_date_any(_text(row, bounds["date"]), True) == (2025, 10, 3)
    assert _parse_date_any(_text(row, bounds["value_date"]), True) == (2025, 10, 3)
    assert _text(row, bounds["description"]) == "SCHOOL 386"
    assert _amount(_text(row, bounds["amount"])) == 1250


def test_header_amount_cell_keeps_adjacent_db_direction_marker():
    header = [
        word("DATE", 45, 74),
        word("PARTICULARS", 87, 159),
        word("VAL", 385, 400),
        word("DATE", 403, 424),
        word("AMOUNT", 466, 508),
        word("BALANCE", 553, 599),
    ]
    bounds = _detect_header_columns([header], 612)["bounds"]
    row = [
        word("03-JUL-25", 386, 424, 200),
        word("1,250.00", 476, 508, 200),
        word("DB", 508.6, 519.7, 200),
    ]
    amount_text = _text(row, bounds["amount"])

    assert _amount(amount_text) == 1250
    assert _amount_direction(_amount(amount_text), "", None, None, amount_text) == "debit"


def test_header_mapping_recognizes_common_non_english_labels():
    header = [
        word("FECHA", 20, 55),
        word("DESCRIPCIÓN", 80, 160),
        word("DÉBITO", 300, 340),
        word("CRÉDITO", 400, 450),
        word("SALDO", 510, 550),
    ]

    columns = _detect_header_columns([header], 612)

    assert columns is not None
    assert set(columns["bounds"]) == {"date", "description", "debit", "credit", "balance"}


def test_month_name_date_is_unambiguous_day_first():
    assert _detect_day_first(["03-JUL-25"]) == (True, False)


def test_sparse_primary_date_is_recognized_as_grouped():
    bounds = {"date": (0, 50), "value_date": (70, 120), "amount": (130, 180)}
    rows = [
        [word("03-JUL-25", 10, 45), word("03-JUL-25", 75, 110), word("10.00", 140, 170)],
        [word("03-JUL-25", 75, 110), word("20.00", 140, 170)],
        [word("03-JUL-25", 75, 110), word("30.00", 140, 170)],
        [word("04-JUL-25", 10, 45), word("04-JUL-25", 75, 110), word("40.00", 140, 170)],
        [word("04-JUL-25", 75, 110), word("40.00", 140, 170)],
    ]

    assert _uses_grouped_primary_dates(rows, bounds, True)
    assert _transaction_date(None, (2025, 7, 4), (2025, 7, 3), True) == (2025, 7, 3)
    assert _transaction_date(None, (2025, 7, 4), (2025, 7, 3), False) == (2025, 7, 4)


def test_amount_direction_uses_statement_sign_and_clear_description_cues():
    from decimal import Decimal

    assert _amount_direction(Decimal("-10"), "", None, None) == "debit"
    assert _amount_direction(Decimal("10"), "cash withdrawal", None, None) == "debit"
    assert _amount_direction(Decimal("10"), "cash deposit", None, None) == "credit"


def test_amount_direction_uses_inline_bank_marker_and_blank_marker_convention():
    from decimal import Decimal

    assert _amount_direction(Decimal("10"), "cash deposit", None, None, "10.00 DB") == "debit"
    assert _amount_direction(Decimal("10"), "cash withdrawal", None, None, "10.00", True) == "credit"
    assert _amount_direction(Decimal("10"), "", None, None, "10.00 CR") == "credit"
    assert _amount_direction(Decimal("-10"), "", None, None, "-10.00 DB", True) == "debit"
    assert _amount_direction(Decimal("-10"), "", None, None, "-10.00", True) == "credit"


def test_marker_scheme_preserves_signed_amounts_in_their_marked_column():
    from decimal import Decimal

    assert _amount_columns(Decimal("-10"), "debit", True) == (Decimal("-10"), None)
    assert _amount_columns(Decimal("-10"), "credit", True) == (None, Decimal("-10"))
    assert _amount_columns(Decimal("-10"), "debit", False) == (Decimal("10"), None)


def test_associate_nearby_balance_on_adjacent_baseline_and_ignore_opening_balance():
    from decimal import Decimal

    rows = [
        [word("4,000.00", 545, 592, 100)],
        [word("opening", 90, 130, 110), word("balance", 132, 165, 110), word("4,000.00", 545, 592, 110)],
        [word("DB", 508, 520, 200)],
        [word("4,000.00", 545, 592, 209.5)],
        [word("DB", 508, 520, 212)],
    ]

    attached = _associate_nearby_balances(rows, [2, 4], (527, 612))

    assert attached == {2: Decimal("4000.00")}


def test_amount_only_layout_uses_description_before_date_when_columns_overlap():
    result = _column_bounds({
        "date_bucket": 384.0,
        "date_width": 37.344,
        "amount_buckets": [500.0],
        "day_first": True,
        "date_format_ambiguous": False,
    })

    assert result is not None
    assert result["layout"] == "amount_only"
    assert result["bounds"]["description"] == (0.0, 380.0)


def test_amount_only_layout_keeps_description_between_date_and_amount():
    result = _column_bounds({
        "date_bucket": 100.0,
        "date_width": 30.0,
        "amount_buckets": [400.0],
        "day_first": True,
        "date_format_ambiguous": False,
    })

    assert result is not None
    assert result["bounds"]["description"] == (134.0, 310.0)
