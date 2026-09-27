"""Country-agnostic building blocks for extending the statement converter
beyond Pakistan-only, single-currency parsing.

IMPORTANT SCOPE NOTE (read before extending BANK_PROFILES with new banks):
This module intentionally contains NOTHING bank-specific. `statement_converter.py`'s
BANK_PROFILES are coordinate-based -- each entry encodes the exact pixel positions
of a specific bank's columns, measured from a real sample PDF of that bank (see
how "ubl", "bop", and "allied" were added: coordinates were read directly out of
real uploaded statements with pdfplumber, not guessed). Adding HBL, Emirates NBD,
ADCB, Al Rajhi, or NCB support requires the same process, using real sample PDFs
from each bank -- none were available when this module was written, so no such
profiles exist yet. Fabricating coordinates without a real sample would produce
code that runs cleanly on synthetic test fixtures but silently misparses real
statements, which is worse than leaving the bank unsupported.

Similarly, this module does not touch OCR or Arabic/RTL text. The existing
parser reads a PDF's embedded text layer positions (pdfplumber word extraction);
a bilingual/scanned statement needs an OCR engine with an Arabic model and
RTL-aware layout reconstruction, which is a different subsystem, not a flag on
this one. That is out of scope here and called out explicitly in this module's
docstrings so a future implementer doesn't mistake "IBAN/date/FX helpers exist"
for "Arabic OCR support exists."

What IS implemented here, and unit-tested with synthetic (clearly-labeled, not
real-bank) fixtures in test_intl_parsing.py:
  - detect_country_from_iban: PK/AE/SA detection from an IBAN string.
  - normalize_date: ISO 8601 normalization across the requested formats, with
    Hijri-pattern detection (detection only -- Hijri-to-Gregorian conversion is
    NOT implemented; see the function docstring for why).
  - merge_fx_lines: generic multi-line FX/card transaction grouping.
  - validate_running_balance: percentage-tolerance balance-chain validation,
    as an alternative to the existing absolute-cent tolerance used for the
    three original single-currency banks.
"""
from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal, InvalidOperation
import re
from typing import Any


# ---------------------------------------------------------------------------
# 1. IBAN country detection
# ---------------------------------------------------------------------------

# Per the ticket's own spec. Real IBAN check-digit/BBAN validation (mod-97) is
# NOT implemented -- this is prefix/shape detection only, matching what the
# ticket asked for ("detect country by IBAN prefix"), not full IBAN validity
# checking. Flagging that distinction explicitly rather than silently
# implying more validation happens than actually does.
# Per the ticket's own spec, but tightened: the ticket's literal
# `[A-Z0-9]{1,30}` is open-ended and provably over-captures trailing
# unrelated text when a single space separates the IBAN from the next label
# (e.g. "...9325 CIF#:" was captured as part of the IBAN in testing --
# see test_extract_iban_does_not_swallow_trailing_label). Real IBANs have a
# fixed length per country (PK=24, AE=23, SA=24 total characters), so the
# BBAN portion is pinned to an exact count instead of an open range.
# Real IBAN check-digit/BBAN validation (mod-97) is still NOT implemented --
# this is prefix/shape/length detection only, matching what the ticket asked
# for ("detect country by IBAN prefix"), not full IBAN validity checking.
_IBAN_PATTERNS: dict[str, re.Pattern[str]] = {
    "PK": re.compile(r"\bPK\d{2}(?:[ ]?[A-Z0-9]){20}\b"),
    "AE": re.compile(r"\bAE\d{2}(?:[ ]?[A-Z0-9]){19}\b"),
    "SA": re.compile(r"\bSA\d{2}(?:[ ]?[A-Z0-9]){20}\b"),
}


def detect_country_from_iban(text: str) -> str | None:
    """Return 'PK', 'AE', or 'SA' if a matching IBAN pattern is found in `text`,
    else None. Tolerates grouping spaces inside the IBAN itself (e.g. "PK26
    UNIL 0112 0104 1000 9325") without collapsing whitespace across the whole
    input first -- doing that would destroy the word boundary between a
    preceding label and the IBAN when they run together with no space
    (e.g. "IBAN:AE07...")."""
    upper = text.upper()
    for country, pattern in _IBAN_PATTERNS.items():
        if pattern.search(upper):
            return country
    return None


def extract_iban(text: str) -> str | None:
    """Return the first matching IBAN substring (PK/AE/SA only), spaces removed."""
    upper = text.upper()
    for pattern in _IBAN_PATTERNS.values():
        match = pattern.search(upper)
        if match:
            return re.sub(r"\s+", "", match.group(0))
    return None


# ---------------------------------------------------------------------------
# 2. Date normalization to ISO 8601
# ---------------------------------------------------------------------------

_EXPLICIT_DATE_FORMATS = (
    "%d-%m-%Y",
    "%d/%m/%Y",
    "%d-%b-%Y",
)

# Hijri years currently fall in the 1440s-1450s (started 622 CE, ~354-day
# year). The ticket's own regex (14[0-9]{2}/\d{1,2}/\d{1,2}) is used verbatim.
_HIJRI_PATTERN = re.compile(r"\b14[0-9]{2}/\d{1,2}/\d{1,2}\b")


def normalize_date(text: str) -> dict[str, Any]:
    """Try explicit DD-MM-YYYY / DD/MM/YYYY / DD-MMM-YYYY formats in order.

    Returns a dict:
      {"iso_date": "YYYY-MM-DD" or None, "is_hijri": bool, "raw": text}

    Hijri handling is DETECTION ONLY, not conversion. Converting a Hijri date
    to a specific Gregorian calendar date requires either an authoritative
    lunar calendar table or an external library (e.g. `hijri-converter`) --
    neither is a dependency of this project today, and different Islamic
    calendar conventions (Umm al-Qura vs. tabular) can disagree by a day
    near month boundaries. Silently picking one and returning a Gregorian
    date would misdate a transaction with no visible warning. Instead, a
    Hijri-shaped date is flagged via is_hijri=True with iso_date=None, so the
    caller can route it to needs_review / manual entry rather than trust a
    fabricated conversion. Add a real conversion library as a scoped,
    separate follow-up if Hijri-dated statements actually turn up in samples.
    """
    stripped = text.strip()
    if _HIJRI_PATTERN.search(stripped):
        return {"iso_date": None, "is_hijri": True, "raw": text}

    compact = re.sub(r"\s+", " ", stripped)
    for fmt in _EXPLICIT_DATE_FORMATS:
        try:
            parsed = datetime.strptime(compact, fmt).date()
            return {"iso_date": parsed.isoformat(), "is_hijri": False, "raw": text}
        except ValueError:
            continue

    # Bounded fallback: pull the first date-shaped token out of noisier text
    # instead of a general fuzzy parser. An unconstrained fuzzy date parser
    # (e.g. dateutil.parser with default settings) will "successfully" parse
    # things that are not dates at all (plain numbers, reference codes) and
    # return a wrong date silently -- that failure mode is worse than
    # returning None for genuinely unparseable text.
    candidates = re.findall(
        r"\d{1,2}[-/][A-Za-z]{3}[-/]\d{2,4}|\d{1,2}[-/]\d{1,2}[-/]\d{2,4}",
        compact,
    )
    for candidate in candidates:
        for fmt in _EXPLICIT_DATE_FORMATS + ("%d-%b-%y", "%d/%m/%y"):
            try:
                parsed = datetime.strptime(candidate, fmt).date()
                return {"iso_date": parsed.isoformat(), "is_hijri": False, "raw": text}
            except ValueError:
                continue

    return {"iso_date": None, "is_hijri": False, "raw": text}


# ---------------------------------------------------------------------------
# 3. Multi-currency / FX line grouping
# ---------------------------------------------------------------------------

_CURRENCY_CODES = ("USD", "GBP", "EUR", "AED", "SAR", "PKR")
_CURRENCY_LINE = re.compile(
    r"(?P<currency>" + "|".join(_CURRENCY_CODES) + r")\s*"
    r"(?P<amount>-?\d{1,3}(?:,\d{3})*(?:\.\d{1,2})?)"
)
_FEE_LINE = re.compile(r"\bfee\b|\bcharges?\b|\bmark[- ]?up\b", re.IGNORECASE)


def merge_fx_lines(lines: list[str], local_currency: str = "PKR") -> dict[str, Any] | None:
    """Merge a foreign-currency line + local-equivalent line (+ optional fee
    line) into one transaction dict.

    This is a GENERIC heuristic operating purely on description text patterns
    (a currency code followed by a number), not tied to any bank's column
    layout -- it can run as a post-processing pass over any bank profile's
    already-extracted description text. It has NOT been validated against a
    real multi-currency statement (none were available); it is unit-tested
    against synthetic fixtures only. Treat it as a starting point to refine
    once real FX/card-transaction samples are available, not as proven
    against real data.

    Returns None if `lines` doesn't contain a recognizable foreign-currency
    line, so callers can fall back to treating the lines as ordinary
    (non-FX) transaction text.
    """
    foreign_amount = foreign_currency = None
    local_amount = None
    fee = None

    for line in lines:
        match = _CURRENCY_LINE.search(line)
        if not match:
            continue
        code = match.group("currency")
        try:
            amount = Decimal(match.group("amount").replace(",", ""))
        except InvalidOperation:
            continue
        if code == local_currency:
            if _FEE_LINE.search(line) and local_amount is not None:
                fee = amount
            elif local_amount is None:
                local_amount = amount
            else:
                fee = amount
        elif foreign_amount is None:
            foreign_amount = amount
            foreign_currency = code

    if foreign_amount is None:
        return None

    return {
        "foreign_amount": float(foreign_amount),
        "foreign_currency": foreign_currency,
        "local_amount": float(local_amount) if local_amount is not None else None,
        "local_currency": local_currency,
        "fee": float(fee) if fee is not None else None,
    }


# ---------------------------------------------------------------------------
# 4. Percentage-tolerance running-balance validation
# ---------------------------------------------------------------------------

def validate_running_balance(
    transactions: list[dict[str, Any]],
    opening_balance: float,
    tolerance_pct: float = 0.5,
) -> list[dict[str, Any]]:
    """Recompute a running balance from `opening_balance` through
    `transactions` (each needing numeric-or-None "debit"/"credit"/"balance"
    keys) and flag any row whose printed balance differs from the expected
    running balance by more than `tolerance_pct` percent of the expected
    balance.

    This is a percentage-based alternative to the fixed 1-cent tolerance
    `parse_statement()` already uses internally for MCB/Samba/FWB/UBL/BOP/
    Allied. It is NOT wired into `parse_statement()` -- that function's
    existing absolute-cent check is stricter and already proven correct
    against six real bank formats (see prior test results: exact match to
    printed closing balances on all of them). Swapping the default tolerance
    from "exact to the cent" to "within 0.5%" is a real behavior change with
    accounting implications (a 0.5%-off balance on a large account could
    still be off by a materially large rupee/dirham/riyal amount and pass
    silently) -- that is a product decision, not something to default
    silently. This function exists so that decision can be made explicitly
    per-country if/when it's needed, rather than baked into the core parser.
    """
    running = Decimal(str(opening_balance))
    results: list[dict[str, Any]] = []
    for txn in transactions:
        debit = Decimal(str(txn.get("debit") or 0))
        credit = Decimal(str(txn.get("credit") or 0))
        expected = running - debit + credit
        printed = txn.get("balance")
        flagged = True
        diff_pct = None
        if printed is not None:
            printed_dec = Decimal(str(printed))
            if expected == 0:
                flagged = printed_dec != 0
                diff_pct = 0.0 if not flagged else None
            else:
                diff_pct = float(abs(expected - printed_dec) / abs(expected) * 100)
                flagged = diff_pct > tolerance_pct
            running = printed_dec
        else:
            running = expected
        results.append({**txn, "expected_balance": float(expected), "balance_diff_pct": diff_pct, "flagged": flagged})
    return results
