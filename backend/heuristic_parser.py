"""Layout-agnostic fallback parser for bank statements with no configured profile.

Only used when parse_statement() doesn't recognise the requested bank profile
(or when no profile was given at all). It statistically guesses where the
date / description / amount columns sit, instead of reading them from a
hand-built BANK_PROFILES entry, and reuses the exact same word-clustering and
amount-parsing helpers as the profile-based parser (imported, not
duplicated) so a fix there benefits both paths.

Every transaction this module produces is unconditionally flagged
needs_review=True, with no exceptions, regardless of how well the balance
chain validates. Column positions here are guessed statistically, not
hand-verified against a real statement the way every BANK_PROFILES entry is
-- see statement_converter.py's profile comments for examples of the kind of
per-bank quirks (signed amounts, OCR-only pages, swapped credit/debit column
order) that only got caught by checking against a real sample. A guess never
earns that same trust, so it never gets to clear its own review flag.

The balance chain still runs here and is reported back as a confidence
score, so a human reviewer -- or the calling API, deciding whether to offer
an AI-vision retry -- knows how much to trust a given result before using it
for anything.

Tested against three real, independently-verified statements (see
HANDOFF_post_smoke_test.md) with their bank profile deliberately ignored, to
check this path's real accuracy rather than just that it runs without
crashing -- see heuristic_test_results.md for the actual numbers.
"""
from __future__ import annotations

from collections import Counter
from datetime import datetime
from decimal import Decimal
import re
from typing import Any

import pdfplumber

from statement_converter import _cluster_rows, _text, _amount, _AMOUNT


def _text_by_x1(row: list[dict[str, Any]], bounds: tuple[float, float]) -> str:
    """Same job as statement_converter._text(), but filters each word by
    its RIGHT edge (x1) falling in bounds, not its left edge (x0).

    Needed specifically for amount columns: they're detected by clustering
    x1 (the right edge, since money is right-aligned -- see _detect_columns
    for why x0 doesn't work there), so the bounds built from that detection
    are x1-anchored too. Filtering those bounds with the ordinary x0-based
    _text() silently measures the wrong edge and pulls in whichever
    column's LEFT edge happens to land in a range that was really defined
    by RIGHT edges -- confirmed against FWB, where this exact mismatch
    made a balance value land in the credit field. Date and description
    stay on the ordinary x0-based _text(), since date-column detection is
    still x0-anchored (see _detect_columns) and was never affected."""
    start, end = bounds
    words = sorted((w for w in row if start <= w["x1"] < end), key=lambda w: w["x0"])
    return " ".join(w["text"] for w in words)

# Shape-only regexes: used purely to locate WHERE dates sit on the page
# (which column), not to parse them yet. _DATE_SHAPE covers a date printed
# as a single token (numeric, month-name, or ISO). _DATE_SHAPE_MULTI_TEXT
# covers the same month-name shape when a bank instead prints it as 2-3
# separate space-separated words (e.g. "02 JUL 2025") -- pdfplumber's
# extract_words() splits on whitespace, so those never show up as one token
# and need their own detection pass over adjacent-word windows.
_DATE_SHAPE = re.compile(
    r"^\d{4}-\d{2}-\d{2}$"                      # ISO: 2025-07-02
    r"|^\d{1,2}[/.\-]\d{1,2}[/.\-]\d{2,4}$"      # numeric: 02/07/2025, 02.07.25
    r"|^\d{1,2}[-/]?[A-Za-z]{3}[-/]?\d{2,4}$",   # month-name, no spaces: 02-Jul-2025
    re.IGNORECASE,
)
_DATE_SHAPE_MULTI_TEXT = re.compile(r"^\d{1,2}\s+[A-Za-z]{3}\s+\d{2,4}$", re.IGNORECASE)
# Same two shapes again, but for stripping matched substrings OUT of
# already-joined description text (see _strip_stray_dates) rather than
# testing a single word/window in isolation -- needs \b-bounded, global
# substitution instead of a fullmatch.
_DATE_INLINE = re.compile(
    r"\b\d{4}-\d{2}-\d{2}\b"
    r"|\b\d{1,2}[/.\-]\d{1,2}[/.\-]\d{2,4}\b"
    r"|\b\d{1,2}[-/]?[A-Za-z]{3}[-/]?\d{2,4}\b",
    re.IGNORECASE,
)
_DATE_INLINE_MULTI = re.compile(r"\b\d{1,2}\s+[A-Za-z]{3}\s+\d{2,4}\b", re.IGNORECASE)

_MONTHS = {
    m.upper(): i
    for i, m in enumerate(
        ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"], start=1
    )
}


def _looks_like_money(text: str) -> bool:
    """Stricter than a bare _AMOUNT match, for column-DETECTION purposes
    only (not for parsing an already-located amount cell, which still uses
    _amount()/_AMOUNT as-is). _AMOUNT's \\d+ fallback branch matches any
    plain digit string, which is correct for parsing a genuine amount cell
    but wrong for deciding WHERE the amount columns are.

    Requires a decimal point or thousands-separator comma, full stop --
    confirmed necessary against two distinct contamination sources on the
    same FWB statement: a long bare-digit account number ("0027013247120001",
    16 digits) and short bare digits from ordinary legal/footer prose
    ("within 15 days", "45 days") both slipping through an earlier, more
    permissive version of this check that allowed short bare-digit runs
    through on the assumption they might be a decimal-less amount. Every
    real amount in every sample statement this project has (MCB, Samba,
    FWB) prints with a decimal point, so that assumption bought no real
    coverage and cost real false positives -- if a future bank genuinely
    prints whole-number amounts with no decimal or grouping at all, that's
    a real gap, not a silently-swallowed one: it would show up as this
    module returning column_detection_failed rather than guessing wrong.
    """
    text = text.replace(" ", "")
    if not _AMOUNT.fullmatch(text):
        return False
    return "," in text or "'" in text or "." in text


def _round_bucket(x: float, size: float = 6.0) -> float:
    return round(x / size) * size


def _zero_to_none(amount: Decimal | None) -> Decimal | None:
    # Real bank statements essentially never print a literal 0.00 in a
    # debit or credit cell that doesn't apply -- they leave it blank. A
    # captured exact zero here almost always means the column bound
    # accidentally reached into an unrelated numeric field instead (found
    # against FWB: a "Doc.ID" column that prints a literal 0 on every row
    # sat just inside the guessed debit-column bound). Treating a parsed
    # zero as "nothing here" rather than "a real zero transaction" fixes
    # that whole class of contamination without needing pixel-perfect
    # column bounds.
    return None if amount == 0 else amount


def _round_amount_bucket(x: float, size: float = 20.0) -> float:
    # Wider than _round_bucket: amount columns are frequently right-aligned
    # (money is), so a token's x0 shifts with its digit count -- "4.80" and
    # "30.00" don't start at the same x-position even in the same column.
    # Confirmed against MCB: a 6pt bucket split one real debit column into
    # two (456.0 and 462.0), which _column_bounds then misread as two
    # separate columns. Genuinely distinct columns in every real profile in
    # statement_converter.py sit 40pt+ apart, so 20pt is wide enough to
    # absorb same-column jitter without merging two different columns.
    return round(x / size) * size


def _strip_stray_dates(text: str) -> str:
    """Remove a second date-shaped column (e.g. a Value Date next to the
    Post/Booking Date this module chose as THE date column) that landed
    inside description bounds. Confirmed necessary against both MCB and FWB
    -- both print two date columns close enough together that a
    statistically-guessed description boundary can't reliably exclude the
    second one on x-position alone."""
    text = _DATE_INLINE_MULTI.sub(" ", text)
    text = _DATE_INLINE.sub(" ", text)
    return re.sub(r"\s+", " ", text).strip()


def _parse_date_any(raw: str, day_first: bool) -> tuple[int, int, int] | None:
    """Best-effort (year, month, day) parse across mixed formats, including
    a month name with spaces instead of punctuation between its parts
    (e.g. "02 JUL 2025", from _text() joining three separate words).

    day_first governs ONLY the ambiguous numeric case (both parts <= 12) --
    resolved once for the whole document by _detect_day_first, not guessed
    per-row, since a single statement uses one convention throughout.
    """
    text = raw.strip()
    m = re.match(r"^(\d{4})-(\d{2})-(\d{2})$", text)
    if m:
        y, mo, d = (int(g) for g in m.groups())
        return (y, mo, d) if 1 <= mo <= 12 and 1 <= d <= 31 else None

    m = re.match(r"^(\d{1,2})\s*[-/]?\s*([A-Za-z]{3})\s*[-/]?\s*(\d{2,4})$", text)
    if m:
        d, mon_name, y = m.groups()
        month = _MONTHS.get(mon_name.upper())
        if month is None:
            return None
        year = int(y) if len(y) == 4 else 2000 + int(y)
        day = int(d)
        return (year, month, day) if 1 <= day <= 31 else None

    m = re.match(r"^(\d{1,2})[/.\-](\d{1,2})[/.\-](\d{2,4})$", text)
    if m:
        a, b, y = (int(g) for g in m.groups())
        year = y if y > 99 else 2000 + y
        if a > 12 and b <= 12:
            day, month = a, b
        elif b > 12 and a <= 12:
            day, month = b, a
        elif day_first:
            day, month = a, b
        else:
            day, month = b, a
        return (year, month, day) if 1 <= month <= 12 and 1 <= day <= 31 else None
    return None


def _date_windows(row: list[dict[str, Any]]) -> list[tuple[float, float, str]]:
    """(x0, x1, joined_text) for every single word OR 2-3-word adjacent
    window in this row that looks date-shaped -- see module docstring for
    why multi-word windows matter (Samba-style spaced dates). x1 (the
    match's right edge) lets the caller measure how wide a real date
    actually is on this specific statement, instead of guessing one fixed
    width for every bank -- see _detect_columns."""
    ordered = sorted(row, key=lambda w: w["x0"])
    hits: list[tuple[float, float, str]] = []
    for i, word in enumerate(ordered):
        if _DATE_SHAPE.match(word["text"]):
            hits.append((word["x0"], word["x1"], word["text"]))
        for span in (2, 3):
            if i + span <= len(ordered):
                window = ordered[i : i + span]
                joined = " ".join(w["text"] for w in window)
                if _DATE_SHAPE_MULTI_TEXT.match(joined):
                    hits.append((window[0]["x0"], window[-1]["x1"], joined))
    return hits


def _detect_day_first(date_texts: list[str]) -> tuple[bool, bool]:
    """Look for at least one date whose first numeric part exceeds 12 --
    that alone proves the convention for numeric dates in this document,
    since no month can be 13+. Returns (day_first, was_ambiguous)."""
    for text in date_texts:
        m = re.match(r"^(\d{1,2})[/.\-](\d{1,2})[/.\-]\d{2,4}$", text.strip())
        if m:
            a, b = int(m.group(1)), int(m.group(2))
            if a > 12:
                return True, False
            if b > 12:
                return False, False
    return True, True  # no disambiguating date found; default to day-first, flagged ambiguous


def _detect_columns(rows: list[list[dict[str, Any]]]) -> dict[str, Any] | None:
    """Statistically locate the date / amount column(s) from a sample of rows."""
    date_x0s: list[float] = []
    date_widths: list[float] = []
    date_texts: list[str] = []
    amount_x0s: list[float] = []

    for row in rows:
        for x0, x1, text in _date_windows(row):
            bucket = _round_bucket(x0)
            date_x0s.append(bucket)
            date_widths.append(x1 - x0)
            date_texts.append(text)
        for word in row:
            if _looks_like_money(word["text"]):
                value = _amount(word["text"].replace(" ", ""))
                if value == 0:
                    # A column that always prints exactly 0 (confirmed:
                    # FWB's Doc.ID field) is not a real debit/credit/
                    # balance column -- see _zero_to_none for the matching
                    # rule applied to actual output values, not just
                    # column detection.
                    continue
                # Monetary values are right-aligned in statement tables.  Use
                # their right edge, rather than x0: a leading minus sign makes
                # a debit start further left than an otherwise identical
                # credit, but it does not move the column's right edge.  Using
                # x0 split Wio/Allied-style signed amount columns into two
                # buckets and made the detector mistake amount+balance for a
                # debit+credit+balance layout.
                amount_x0s.append(_round_amount_bucket(word["x1"]))

    if not date_x0s:
        return None

    date_bucket, date_hits = Counter(date_x0s).most_common(1)[0]
    if date_hits < 3:  # too few date-shaped tokens at any single position to trust
        return None

    # Real width of a date at THIS bucket, not a fixed guess -- MCB's
    # single-token "01-SEP-25" and Samba's three-word "02 JUL 2025" need
    # very different column widths, and a fixed number sized for one broke
    # the other (confirmed: MCB's date column then reached far enough right
    # to swallow a second, adjacent Effect Date column). Max, not average,
    # so a date column is never too narrow for its widest real entry.
    widths_at_bucket = [w for x0, w in zip(date_x0s, date_widths) if x0 == date_bucket]
    date_width = max(widths_at_bucket) if widths_at_bucket else 40.0

    # Amount columns: keep buckets that recur often enough to be a real
    # column rather than a one-off number that happened to look like money
    # (e.g. a reference or STAN number). Threshold is relative to how many
    # date hits we found, since that's our best estimate of transaction count.
    # A debit-only or credit-only column, by nature, only fires on the
    # subset of rows where that side applies -- confirmed against FWB,
    # where debit legitimately appears on only 2 of 4 real transactions
    # (the other 2 are credit-only) and was being filtered out entirely by
    # too strict a threshold. /4 and a floor of 2 is deliberately more
    # lenient than a naive "most rows should have this" assumption would
    # suggest, precisely because debit/credit are mutually exclusive by
    # definition, not because column detection in general should be loose.
    min_hits = max(2, date_hits // 4)
    amount_buckets = sorted(
        bucket for bucket, hits in Counter(amount_x0s).items() if hits >= min_hits
    )

    day_first, ambiguous = _detect_day_first(date_texts)

    return {
        "date_bucket": date_bucket,
        "date_width": date_width,
        "amount_buckets": amount_buckets,
        "day_first": day_first,
        "date_format_ambiguous": ambiguous,
        "date_sample_size": date_hits,
    }


def _bounds_for_buckets(buckets: list[float], left_fallback: float = 90.0, right_fallback: float = 30.0) -> list[tuple[float, float]]:
    """(start, end) for each bucket in a left-to-right ordered list, using
    the midpoint between neighbouring buckets as their shared boundary.

    This is deliberately edge-semantics-agnostic: it works the same whether
    a bucket is a column's left edge (x0) or right edge (x1), because either
    way, two adjacent columns' buckets straddle the real gap between them,
    so the midpoint is a safe divider regardless of which edge is being
    tracked. A fixed offset was used here before and broke completely the
    moment amount-column detection switched from x0 to x1 (see
    HANDOFF_LATEST_FIXES.md) -- the offset math implicitly assumed a bucket
    was always a left edge, which stopped being true. Confirmed against the
    same regression check this project already uses (MCB/Samba/FWB with
    their bank profile hidden): this version restores 100%/100%/77.6%
    confidence, matching pre-x1-switch results, while keeping the x1
    change's real benefit for signed single-amount columns.

    The first bucket's left edge and the last bucket's right edge have no
    neighbour to split a midpoint with, so they use a fixed fallback pad
    instead, generous enough to catch that column's widest realistic entry.
    """
    bounds = []
    for i, b in enumerate(buckets):
        left = (buckets[i - 1] + b) / 2 if i > 0 else b - left_fallback
        right = (b + buckets[i + 1]) / 2 if i + 1 < len(buckets) else b + right_fallback
        bounds.append((left, right))
    return bounds


def _column_bounds(columns: dict[str, Any]) -> dict[str, Any] | None:
    """Turn detected bucket positions into (start, end) bounds, and decide
    the layout: debit+credit+balance, amount+balance, or amount-only."""
    date_start = columns["date_bucket"] - 4
    date_end = columns["date_bucket"] + columns["date_width"] + 4
    amount_buckets = columns["amount_buckets"]
    if not amount_buckets:
        return None

    if len(amount_buckets) >= 3:
        # Rightmost three = debit, credit, balance in that left-to-right
        # order. Anything further left is treated as noise (a reference or
        # STAN number that happened to look numeric) rather than a fourth
        # real column, since every profile in statement_converter.py has at
        # most three money columns -- see BANK_PROFILES for real examples
        # of that shape. Deliberately excluded from the boundary math too,
        # not just from layout selection -- a noise bucket's position isn't
        # trustworthy enough to help define where a real column starts.
        debit_bound, credit_bound, balance_bound = _bounds_for_buckets(amount_buckets[-3:])
        layout = "debit_credit_balance"
        bounds = {
            "date": (date_start, date_end),
            "description": (date_end, debit_bound[0]),
            "debit": debit_bound,
            "credit": credit_bound,
            "balance": balance_bound,
        }
    elif len(amount_buckets) == 2:
        amount_bound, balance_bound = _bounds_for_buckets(amount_buckets)
        layout = "amount_balance"
        bounds = {
            "date": (date_start, date_end),
            "description": (date_end, amount_bound[0]),
            "amount": amount_bound,
            "balance": balance_bound,
        }
    else:
        (amount_bound,) = _bounds_for_buckets(amount_buckets)
        layout = "amount_only"
        bounds = {
            "date": (date_start, date_end),
            "description": (date_end, amount_bound[0]),
            "amount": amount_bound,
        }
    return {"layout": layout, "bounds": bounds}


def parse_statement_heuristic(pdf_path: str, sample_pages: int = 15) -> dict[str, Any]:
    """Best-effort extraction for a bank with no BANK_PROFILES entry.

    Returns a dict (not a bare transaction list, unlike parse_statement()):
    {
      "transactions": [...],       # each item always has needs_review=True
      "layout_detected": str | None,
      "confidence": float | None,  # fraction of rows whose balance validated; None if no balance column found
      "date_format_ambiguous": bool,
      "column_detection_failed": bool,
    }
    A column_detection_failed=True result (empty transactions) means this
    document couldn't be read at all this way -- e.g. no text layer (a
    scanned PDF, needing the separate OCR path), or too few date-shaped
    tokens to find a column. The caller should treat that as "ask the user
    to try harder" territory, per PRODUCT_VISION_AND_ROADMAP.md, not as
    zero transactions found.
    """
    with pdfplumber.open(pdf_path) as pdf:
        pages = pdf.pages
        sample_rows: list[list[dict[str, Any]]] = []
        for page in pages[:sample_pages]:
            sample_rows.extend(_cluster_rows(page.extract_words(x_tolerance=1, y_tolerance=1)))

        columns = _detect_columns(sample_rows)
        if columns is None:
            return {
                "transactions": [], "layout_detected": None, "confidence": None,
                "date_format_ambiguous": False, "column_detection_failed": True,
            }

        layout_info = _column_bounds(columns)
        if layout_info is None:
            return {
                "transactions": [], "layout_detected": None, "confidence": None,
                "date_format_ambiguous": columns["date_format_ambiguous"], "column_detection_failed": True,
            }

        bounds = layout_info["bounds"]
        layout = layout_info["layout"]
        day_first = columns["day_first"]

        transactions: list[dict[str, Any]] = []
        current: dict[str, Any] | None = None
        for page in pages:
            rows = _cluster_rows(page.extract_words(x_tolerance=1, y_tolerance=1))
            for row in rows:
                date_text = _text(row, bounds["date"])
                parsed = _parse_date_any(date_text, day_first) if date_text else None
                # Require BOTH a plausible date AND a real amount somewhere
                # in a detected money column before accepting a row as a new
                # transaction -- a prose line mentioning a date (e.g. a
                # "Statement Date: 07 Jan 2026" header) can match the date
                # shape alone, but won't also carry a number in the amount
                # column position, so this second check filters it out. The
                # profile-based parser doesn't need this extra guard because
                # its column bounds are hand-verified, not guessed.
                has_amount = any(
                    _amount(_text_by_x1(row, bounds[key])) is not None
                    for key in bounds if key not in ("date", "description")
                )
                if parsed and has_amount:
                    if current is not None:
                        transactions.append(current)
                    year, month, day = parsed
                    try:
                        iso_date = datetime(year, month, day).date().isoformat()
                    except ValueError:
                        iso_date = None
                    if layout == "debit_credit_balance":
                        debit = _zero_to_none(_amount(_text_by_x1(row, bounds["debit"])))
                        credit = _zero_to_none(_amount(_text_by_x1(row, bounds["credit"])))
                        balance = _amount(_text_by_x1(row, bounds["balance"]))
                    elif layout == "amount_balance":
                        signed = _amount(_text_by_x1(row, bounds["amount"]))
                        debit = _zero_to_none(-signed if (signed is not None and signed < 0) else None)
                        credit = _zero_to_none(signed if (signed is not None and signed >= 0) else None)
                        balance = _amount(_text_by_x1(row, bounds["balance"]))
                    else:  # amount_only
                        signed = _amount(_text_by_x1(row, bounds["amount"]))
                        debit = _zero_to_none(-signed if (signed is not None and signed < 0) else None)
                        credit = _zero_to_none(signed if (signed is not None and signed >= 0) else None)
                        balance = None
                    current = {
                        "date": iso_date,
                        "description_parts": [_strip_stray_dates(_text(row, bounds["description"]))],
                        "debit": debit,
                        "credit": credit,
                        "balance": balance,
                    }
                elif current is not None:
                    continuation = _strip_stray_dates(_text(row, bounds["description"]))
                    if continuation:
                        current["description_parts"].append(continuation)
        if current is not None:
            transactions.append(current)

    # Final pass: infer a missing balance from the prior balance and this
    # row's debit/credit, exactly like the profile-based parser's own final
    # pass (see parse_statement in statement_converter.py) -- an inferred
    # balance changes nothing about needs_review here (already always True),
    # but it does matter for the confidence score below: without it, one
    # row with no printed balance breaks the chain for every row after it,
    # not just that one row.
    prior_balance: Decimal | None = None
    checked = 0
    matched = 0
    result: list[dict[str, Any]] = []
    for t in transactions:
        debit = t["debit"] or Decimal("0")
        credit = t["credit"] or Decimal("0")
        balance = t["balance"]
        if balance is None and prior_balance is not None and (t["debit"] or t["credit"]):
            balance = prior_balance - debit + credit
        elif balance is not None and prior_balance is not None:
            checked += 1
            if abs((prior_balance - debit + credit) - balance) <= Decimal("0.01"):
                matched += 1
        result.append({
            "date": t["date"],
            "description": re.sub(r"\s+", " ", " ".join(t["description_parts"])).strip(),
            "debit": float(t["debit"]) if t["debit"] is not None else None,
            "credit": float(t["credit"]) if t["credit"] is not None else None,
            "balance": float(balance) if balance is not None else None,
            "needs_review": True,  # unconditional -- see module docstring
        })
        if balance is not None:
            prior_balance = balance

    return {
        "transactions": result,
        "layout_detected": layout,
        "confidence": (matched / checked) if checked else None,
        "date_format_ambiguous": columns["date_format_ambiguous"],
        "column_detection_failed": False,
    }
