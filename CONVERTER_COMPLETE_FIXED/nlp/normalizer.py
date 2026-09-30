from __future__ import annotations

import re

_WHITESPACE_RE = re.compile(r"\s+")
_REPEATED_SEPARATOR_RE = re.compile(r"[\-_/]{2,}")


def normalize(description: str) -> str:
    """Produce a normalized representation for matching, alongside
    (never instead of) the original description.

    Deliberately conservative for this first version, per spec sections
    9-10: lowercase, collapse whitespace, collapse repeated separators.
    Does NOT strip dates, amounts, cheque numbers, branch codes, or
    reference numbers -- distinguishing genuinely-safe-to-strip "noise"
    (a payment-provider prefix, an OCR artifact) from meaningful
    reference data isn't something to guess at without real transaction
    samples showing what's actually noise across real statements. That's
    exactly the kind of guess this project avoids making ahead of real
    data (same reasoning as not building Phase 2 classification yet).

    More aggressive normalization (known-prefix removal, OCR correction)
    is a deliberate next step once real accepted/reviewed transactions
    show what's safe -- not implemented here.
    """
    text = description.strip().lower()
    text = _REPEATED_SEPARATOR_RE.sub("-", text)
    text = _WHITESPACE_RE.sub(" ", text)
    return text.strip()
