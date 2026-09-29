from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


class Decision(str, Enum):
    ACCEPT = "accept"
    REVIEW = "review"


class Method(str, Enum):
    """Which tier actually produced the result -- never claim a higher
    tier ran than actually did (spec section 33: no fake AI labels)."""

    RULE = "rule"
    FUZZY_MATCH = "fuzzy_match"
    CLASSIFIER = "classifier"
    SEMANTIC_MATCH = "semantic_match"
    NONE = "none"


@dataclass
class TransactionInput:
    """What the pipeline needs for one transaction. Deliberately a
    subset of the full transaction row -- this package doesn't need to
    know about debit/credit/balance to do text analysis, and keeping it
    narrow makes the module easy to unit-test without a database."""

    description: str
    date: str | None = None


@dataclass
class TransactionAnalysis:
    """Every evidence score kept separate, per spec section 22: never
    collapse these into a single averaged 'confidence' number. A
    caller (or a human debugging a false accept/review) can see exactly
    which tier decided what."""

    original_description: str
    normalized_description: str
    method: Method
    rule_label: str | None = None
    rule_confidence: float | None = None
    fuzzy_match_text: str | None = None
    fuzzy_similarity: float | None = None
    # Reserved for tiers not yet implemented (see pipeline.py). Left as
    # explicit None rather than omitted, so callers and tests can see
    # at a glance which tiers a given result did/didn't use.
    classifier_label: str | None = None
    classifier_probability: float | None = None
    semantic_similarity: float | None = None
    decision: Decision = Decision.REVIEW
    review_reasons: list[str] = field(default_factory=list)
