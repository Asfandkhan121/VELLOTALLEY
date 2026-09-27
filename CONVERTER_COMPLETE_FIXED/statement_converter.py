"""Coordinate-based parsers for the supplied Pakistani bank statements.

The profiles deliberately hold page coordinates rather than bank-specific parsing
code.  Adding a bank is therefore normally a configuration change.
"""
from __future__ import annotations

from collections import defaultdict
from datetime import datetime
from decimal import Decimal, InvalidOperation
import re
from typing import Any

import pdfplumber


BANK_PROFILES: dict[str, dict[str, Any]] = {
    "mcb": {
        "name": "MCB Bank Limited",
        "columns": {"date": (0, 50), "description": (121, 430), "debit": (440, 490), "credit": (500, 550), "balance": (560, 612)},
        "date_formats": ("%d-%b-%y",),
        "footer_markers": ("closing ledger balance", "total dr transactions", "total cr transactions", "sum of dr transactions"),
    },
    "samba": {
        "name": "Samba Bank Ltd",
        "columns": {"date": (30, 90), "description": (265, 325), "debit": (380, 435), "credit": (440, 495), "balance": (500, 560)},
        "date_formats": ("%d %b %Y",),
        "footer_markers": ("balance at period end",),
    },
    "fwb": {
        "name": "First Women Bank",
        "columns": {"date": (15, 65), "description": (108, 315), "debit": (365, 425), "credit": (435, 500), "balance": (505, 570)},
        "date_formats": ("%d/%b/%y", "%d/%m/%Y"),
        "footer_markers": ("total dr trans", "closing balance", "this account statement"),
    },
    "ubl": {
        "name": "United Bank Limited",
        "columns": {"date": (0, 55), "description": (80, 360), "debit": (440, 530), "credit": (530, 620), "balance": (620, 695)},
        "date_formats": ("%d-%b-%Y",),
        "footer_markers": ("closing balance", "total withdrawals & total deposits"),
    },
    "bop": {
        "name": "The Bank of Punjab",
        "columns": {"date": (0, 105), "description": (155, 305), "debit": (375, 420), "credit": (420, 480), "balance": (480, 560)},
        "date_formats": ("%d/%m/%Y",),
        "footer_markers": ("closing balance", "end of statement"),
    },
    "allied": {
        "name": "Allied Bank Limited",
        # Allied prints one signed amount column (trailing "-" marks a debit)
        # instead of separate Debit/Credit columns, and never prints a running
        # balance per row -- only a period-start figure once per page header.
        # "amount" replaces "debit"/"credit" for this profile; see parse_statement.
        "columns": {"date": (0, 96), "description": (96, 365), "amount": (365, 425), "balance": (900, 950)},
        "date_formats": ("%d %b %y",),
        "footer_markers": ("balance at period end",),
    },
    "wio": {
        "name": "Wio Bank",
        # UAE. One signed amount column ("Amount (Incl. VAT)"), leading "-"
        # marks a debit -- same single-column model as Allied, but leading
        # minus instead of trailing. Date column narrowed to (0,40): the
        # page header's "FROM 01/02/2025 TO 28/02/2025" line has its first
        # date at x0=45, just past a naive (0,75) bound, and was getting
        # misread as a transaction, swallowing the whole account-summary
        # block into its description. Real transaction dates sit at x0=23.
        "columns": {"date": (0, 40), "description": (75, 420), "amount": (420, 485), "balance": (485, 570)},
        "date_formats": ("%d/%m/%Y",),
        "footer_markers": ("please review this account statement",),
    },
    "adib": {
        "name": "Abu Dhabi Islamic Bank",
        # Credit column narrowed to end at 498, not 545: at (500,545) it
        # also swallowed the adjacent Balance figure, and _amount() (which
        # returns the LAST number found in a column's joined text) silently
        # returned the balance instead of the real (usually 0.00) credit.
        "columns": {"date": (30, 110), "description": (150, 455), "debit": (455, 498), "credit": (498, 525), "balance": (525, 620)},
        "date_formats": ("%d-%m-%Y",),
        "footer_markers": ("disclaimer",),
    },
    "aaib": {
        # Bank name not printed on the statement itself (uploaded as
        # "Weex_AAIB_aed.pdf"); UAE, AED. Uses ISO dates, unlike every other
        # profile here. Debits are printed with a leading "-" even though
        # they already sit in a dedicated Debit column (credits show no
        # sign) -- unlike every other two-column profile, where the column
        # position alone conveys debit vs. credit and printed magnitudes are
        # unsigned. See the abs() call on debit/credit in parse_statement.
        "name": "AAIB (UAE)",
        "columns": {"date": (0, 70), "description": (70, 300), "debit": (300, 400), "credit": (400, 505), "balance": (505, 600)},
        "date_formats": ("%Y-%m-%d",),
        "footer_markers": ("end of statement",),
        "unsign_debit_credit": True,
    },
    "maerki": {
        # Switzerland. Maerki Baumann & Co. AG "Position statement" PDFs
        # have NO embedded text layer at all (confirmed: pdfplumber extracts
        # 0 characters) -- they are scanned/rendered images. Coordinates
        # below were measured from real OCR output (tesseract, 300 DPI),
        # not a text layer -- see ocr_extraction.py. requires_ocr routes
        # parse_statement() through the OCR fallback for every page of this
        # profile, not just pages where a text layer happens to be empty.
        "name": "Maerki Baumann & Co. AG",
        "columns": {"date": (0, 85), "description": (85, 285), "debit": (330, 410), "credit": (410, 505), "balance": (505, 580)},
        "date_formats": ("%d.%m.%y",),
        "footer_markers": ("discrepancies",),
        "requires_ocr": True,
        "ocr_lang": "eng",
    },
    "pingan": {
        # Ping An Bank (China), FTN USD statement. Its transaction timestamp
        # is a compact YYYYMMDDHHMMSS value; only its calendar-date portion is
        # exported. Income and expense are distinct columns.
        "name": "Ping An Bank",
        "columns": {"date": (20, 100), "description": (485, 835), "credit": (125, 205), "debit": (230, 350), "balance": (385, 465)},
        "date_formats": ("%Y%m%d%H%M%S",),
        "footer_markers": (),
    },
}

_AMOUNT = re.compile(r"\(?-?(?:\d{1,3}(?:[,']\d{2,3})+|\d+)(?:\.\d{1,2})?-?\)?")


def _cluster_rows(words: list[dict[str, Any]], tolerance: float = 3.0) -> list[list[dict[str, Any]]]:
    """Cluster words that share a printed baseline into visual rows."""
    rows: list[list[dict[str, Any]]] = []
    for word in sorted(words, key=lambda item: (item["top"], item["x0"])):
        if not rows or abs(word["top"] - rows[-1][0]["top"]) > tolerance:
            rows.append([word])
        else:
            rows[-1].append(word)
    return rows


def _in_column(row: list[dict[str, Any]], bounds: tuple[float, float]) -> list[dict[str, Any]]:
    start, end = bounds
    return [word for word in row if word["x0"] >= start and word["x0"] < end]


def _text(row: list[dict[str, Any]], bounds: tuple[float, float]) -> str:
    # Re-sort by x0 rather than trusting row order: _cluster_rows sorts
    # globally by (top, x0) before clustering, so when two physical
    # sub-lines with slightly different tops get merged into one row (which
    # happens routinely with OCR-sourced words -- baseline detection isn't
    # pixel-perfect), all of one sub-line's words can sort before all of the
    # other's regardless of their actual left-to-right x0 order, scrambling
    # word order within the merged row (reproduced: "Transfer Interactive
    # Brokers LLC" coming back as "LLC Transfer Interactive Brokers"). This
    # re-sort is a no-op for already-x0-ordered rows (the normal text-layer
    # case), so it's safe for every existing profile.
    return " ".join(word["text"] for word in sorted(_in_column(row, bounds), key=lambda w: w["x0"]))


def _date_from(text: str, formats: tuple[str, ...]) -> str | None:
    compact = re.sub(r"\s+", " ", text.strip()).upper()
    for candidate in (compact, *re.findall(r"\d{14}|\d{2}[-/]?[A-Z]{3}[-/]?\d{2,4}|\d{2}\s+[A-Z]{3}\s+\d{4}|\d{2}/\d{2}/\d{4}", compact)):
        for date_format in formats:
            try:
                return datetime.strptime(candidate, date_format).date().isoformat()
            except ValueError:
                pass
    return None


def _amount(text: str) -> Decimal | None:
    matches = _AMOUNT.findall(text.replace(" ", ""))
    if not matches:
        return None
    raw = matches[-1]
    negative = raw.startswith("(") or raw.startswith("-") or raw.endswith("-")
    try:
        value = Decimal(raw.strip("()-").replace(",", "").replace("'", ""))
    except InvalidOperation:
        return None
    return -value if negative else value


def _opening_balance(rows: list[list[dict[str, Any]]], profile: dict[str, Any]) -> Decimal | None:
    """Read a labelled opening balance without treating account-header numbers as money."""
    balance_col = profile["columns"]["balance"]
    for index, row in enumerate(rows):
        label = " ".join(word["text"] for word in row).lower()
        if "opening balance" in label or "balance at per" in label or "balance b/f" in label:
            for nearby in rows[index : index + 3]:
                value = _amount(_text(nearby, balance_col))
                if value is not None:
                    return value
            value = _amount(label)
            if value is not None:
                return value
    return None


def _as_number(value: Decimal | None) -> float | None:
    return float(value) if value is not None else None


def parse_statement(pdf_path: str, bank_profile: str) -> list[dict[str, Any]]:
    """Extract and validate transactions from a supported bank statement (see BANK_PROFILES).

    Returned debit and credit values use the statement's account perspective:
    debit reduces the balance and credit increases it.  A missing printed balance
    is inferred only when the preceding balance and transaction amount are known,
    and that row remains flagged for review.

    Some profiles (currently just "maerki") set requires_ocr=True because the
    PDF has no embedded text layer at all -- every page is OCR'd via
    ocr_extraction.ocr_words_for_page instead of pdfplumber's extract_words.
    That import is deferred to inside this function so parsing any of the
    other, text-layer-based profiles never requires pytesseract/pdf2image to
    be installed.
    """
    try:
        profile = BANK_PROFILES[bank_profile.lower()]
    except KeyError as exc:
        raise ValueError(f"Unknown bank profile: {bank_profile}. Choose from {', '.join(BANK_PROFILES)}") from exc

    requires_ocr = profile.get("requires_ocr", False)
    ocr_lang = profile.get("ocr_lang", "eng")
    if requires_ocr:
        from ocr_extraction import ocr_words_for_page

    transactions: list[dict[str, Any]] = []
    prior_balance: Decimal | None = None
    # Kept outside the page loop: a transaction's continuation lines (sender
    # details, STAN numbers, slip counts) can legitimately be the first rows
    # printed on the *next* page, and must still attach to this transaction
    # rather than being dropped when the page changes.
    current: dict[str, Any] | None = None
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            if requires_ocr:
                words = ocr_words_for_page(pdf_path, page.page_number, lang=ocr_lang)
            else:
                words = page.extract_words(x_tolerance=1, y_tolerance=1)
            rows = _cluster_rows(words)
            page_opening = _opening_balance(rows, profile)
            if prior_balance is None and page_opening is not None:
                prior_balance = page_opening

            # footer_started stays page-scoped on purpose: footer/summary
            # markers only ever appear once, near the end of the statement,
            # and should not suppress rows on a later page.
            footer_started = False
            for row in rows:
                row_text = " ".join(word["text"] for word in row).lower()
                if any(marker in row_text for marker in profile["footer_markers"]):
                    footer_started = True
                    continue
                if footer_started:
                    continue
                date = _date_from(_text(row, profile["columns"]["date"]), profile["date_formats"])
                if date:
                    if current is not None:
                        transactions.append(current)
                    if "amount" in profile["columns"]:
                        # Single signed-amount column (e.g. Allied Bank): a
                        # trailing "-" on the printed figure marks a debit;
                        # anything else (including 0.00) is a credit.
                        signed = _amount(_text(row, profile["columns"]["amount"]))
                        debit = -signed if (signed is not None and signed < 0) else None
                        credit = signed if (signed is not None and signed >= 0) else None
                    else:
                        debit = _amount(_text(row, profile["columns"]["debit"]))
                        credit = _amount(_text(row, profile["columns"]["credit"]))
                        if profile.get("unsign_debit_credit"):
                            # AAIB prints debits with a leading "-" even
                            # though they already sit in a dedicated Debit
                            # column (unlike every other two-column profile,
                            # where column position alone conveys debit vs.
                            # credit and printed magnitudes are unsigned).
                            # Opt-in per profile so this can't silently mask
                            # a real sign issue in any other bank.
                            if debit is not None:
                                debit = abs(debit)
                            if credit is not None:
                                credit = abs(credit)
                    current = {
                        "date": date,
                        "description_parts": [_text(row, profile["columns"]["description"])],
                        "debit": debit,
                        "credit": credit,
                        "balance": _amount(_text(row, profile["columns"]["balance"])),
                    }
                elif current is not None:
                    continuation = _text(row, profile["columns"]["description"])
                    if continuation:
                        current["description_parts"].append(continuation)
        # Finalize once, after the last page, not after every page — the
        # transaction still open at a page boundary may gain more
        # continuation lines from the next page.
        if current is not None:
            transactions.append(current)

    result: list[dict[str, Any]] = []
    for transaction in transactions:
        debit = transaction["debit"] or Decimal("0")
        credit = transaction["credit"] or Decimal("0")
        balance = transaction["balance"]
        inferred = False
        if balance is None and prior_balance is not None and (debit or credit):
            balance = prior_balance - debit + credit
            inferred = True
        expected = prior_balance - debit + credit if prior_balance is not None else None
        invalid = (
            balance is None
            or (expected is not None and abs(expected - balance) > Decimal("0.01"))
            or inferred
        )
        result.append({
            "date": transaction["date"],
            "description": re.sub(r"\s+", " ", " ".join(transaction["description_parts"])).strip(),
            "debit": _as_number(transaction["debit"]),
            "credit": _as_number(transaction["credit"]),
            "balance": _as_number(balance),
            "needs_review": bool(invalid),
        })
        if balance is not None:
            prior_balance = balance
    return result
