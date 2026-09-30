"""Regression tests for ocr_extraction.py and the "maerki" OCR-backed profile.

Unlike test_intl_parsing.py's synthetic fixtures, these run against the real
uploaded Maerki Baumann PDFs (confirmed to have zero embedded text layer --
pdfplumber extracts 0 characters from all four). If those files aren't
present at the hardcoded paths below (e.g. running this outside the session
that had them uploaded), the OCR tests are skipped rather than failed, since
this module has no synthetic substitute for "a PDF with no text layer" that
would actually exercise pdf2image + tesseract meaningfully.
"""
import os
import sys
from decimal import Decimal

sys.path.insert(0, os.path.dirname(__file__))

SAMPLES = {
    "usd": ("/mnt/user-data/uploads/1787428729145_USD_Account_Statement.pdf", Decimal("108.83")),
    "aed": ("/mnt/user-data/uploads/1787428729147_AED_Account_Statement.pdf", Decimal("-19.00")),
    "eur": ("/mnt/user-data/uploads/1787428729147_EUR_Account_Statement.pdf", Decimal("972.50")),
    "gbp": ("/mnt/user-data/uploads/1787428729148_GBP_Account_Statement.pdf", Decimal("15.61")),
}


def _samples_available() -> bool:
    return all(os.path.exists(path) for path, _ in SAMPLES.values())


def test_amount_parses_swiss_apostrophe_thousands_separator():
    from statement_converter import _amount
    assert _amount("100'132.10") == Decimal("100132.10")
    assert _amount("3'730.52") == Decimal("3730.52")
    assert _amount("-23'158.50") == Decimal("-23158.50")
    # comma format (all other profiles) must remain unaffected
    assert _amount("257,925.11") == Decimal("257925.11")
    assert _amount("200,000.00-") == Decimal("-200000.00")


def test_text_reorders_scrambled_ocr_row_by_x0():
    # Reproduces the real bug: two physical sub-lines with slightly
    # different "top" values merge into one _cluster_rows row, and without
    # re-sorting, words can come out in original-row order rather than true
    # left-to-right reading order.
    from statement_converter import _text
    row = [
        {"text": "LLC", "x0": 207, "top": 417.0},
        {"text": "Transfer", "x0": 92, "top": 417.8},
        {"text": "Interactive", "x0": 128, "top": 417.8},
        {"text": "Brokers", "x0": 173, "top": 417.8},
    ]
    assert _text(row, (85, 285)) == "Transfer Interactive Brokers LLC"


def test_maerki_usd_statement_reconciles_exactly():
    if not _samples_available():
        print("SKIP (sample PDFs not present in this environment)")
        return
    from statement_converter import parse_statement
    path, expected_close = SAMPLES["usd"]
    txns = parse_statement(path, "maerki")
    assert len(txns) == 15
    assert all(not t["needs_review"] for t in txns), "unexpected needs_review flags"
    assert Decimal(str(txns[-1]["balance"])) == expected_close
    # spot-check a value with a Swiss thousands separator survived intact
    debit_values = [t["debit"] for t in txns if t["debit"]]
    assert 100132.1 in debit_values, "100'132.10 was truncated"


def test_maerki_aed_eur_gbp_statements_reconcile_exactly():
    if not _samples_available():
        print("SKIP (sample PDFs not present in this environment)")
        return
    from statement_converter import parse_statement
    for label in ("aed", "eur", "gbp"):
        path, expected_close = SAMPLES[label]
        txns = parse_statement(path, "maerki")
        assert len(txns) > 0, f"{label}: no transactions parsed"
        assert all(not t["needs_review"] for t in txns), f"{label}: unexpected needs_review flags"
        assert Decimal(str(txns[-1]["balance"])) == expected_close, f"{label}: balance mismatch"


def test_arabic_language_pack_recognizes_real_arabic_script():
    # Not a bank-statement test -- confirms the "ara" tesseract pack is
    # installed and returns actual Arabic-script text, using the real Wio
    # Bank PDF's footer as a source of genuine Arabic text. Does not assert
    # perfect transcription (OCR accuracy on small/stylized text varies --
    # see HANDOFF for the honest finding on this) -- only that Arabic-script
    # characters come back at all, proving the language pack is wired up.
    wio_path = "/mnt/user-data/uploads/1787428742172_2025_February_statement.pdf"
    if not os.path.exists(wio_path):
        print("SKIP (sample PDF not present in this environment)")
        return
    from ocr_extraction import ocr_words_for_page
    words = ocr_words_for_page(wio_path, 1, lang="eng+ara")
    arabic_words = [w for w in words if any("\u0600" <= ch <= "\u06FF" for ch in w["text"])]
    assert len(arabic_words) > 0, "no Arabic-script text recognized -- is tesseract-ocr-ara installed?"


def test_ocr_words_for_page_raises_clear_error_for_missing_language_pack():
    wio_path = "/mnt/user-data/uploads/1787428742172_2025_February_statement.pdf"
    if not os.path.exists(wio_path):
        print("SKIP (sample PDF not present in this environment)")
        return
    from ocr_extraction import ocr_words_for_page
    try:
        ocr_words_for_page(wio_path, 1, lang="fra")  # French pack not installed
        raised = False
    except RuntimeError as exc:
        raised = "fra" in str(exc)
    assert raised, "expected a clear RuntimeError naming the missing language pack"


if __name__ == "__main__":
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
