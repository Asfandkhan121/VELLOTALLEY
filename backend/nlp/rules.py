from __future__ import annotations

import re

from .models import Method

# Generic, bank-agnostic transaction-type keywords -- these describe the
# CHANNEL or TYPE of transaction (per spec section 11), not an accounting
# classification. Deliberately a small, conservative starting set of
# terms that are safe to recognize regardless of which bank or country a
# statement comes from, rather than merchant-specific guesses that would
# need real data to validate. Word-boundary matched to avoid false
# positives against substrings of unrelated merchant names.
_KNOWN_TRANSACTION_TYPES: tuple[tuple[str, str], ...] = (
    (r"\batm\b", "atm"),
    (r"\bwithdrawal\b", "cash_withdrawal"),
    (r"\bbank charg", "bank_fee"),
    (r"\bservice charg", "bank_fee"),
    (r"\binterest\b", "interest"),
    (r"\bsalary\b", "salary"),
    (r"\bpayroll\b", "salary"),
    (r"\bibft\b", "transfer"),
    (r"\btransfer\b", "transfer"),
    (r"\bpos\b", "card_purchase"),
    (r"\butility\b", "utility"),
)

_COMPILED = tuple((re.compile(pattern), label) for pattern, label in _KNOWN_TRANSACTION_TYPES)


def match_rule(normalized_description: str) -> tuple[str, float] | None:
    """Returns (label, confidence) if a known, reliable pattern matches;
    None otherwise. Confidence is fixed and high for every rule match --
    per spec section 11, this tier should only fire when reliable, not
    produce a graded score. If nothing matches, the pipeline moves on to
    fuzzy matching rather than guessing here.
    """
    for pattern, label in _COMPILED:
        if pattern.search(normalized_description):
            return label, 0.98
    return None


__all__ = ["match_rule", "Method"]
