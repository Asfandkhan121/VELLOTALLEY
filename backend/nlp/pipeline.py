from __future__ import annotations

from .fuzzy_matcher import best_match
from .models import Decision, Method, TransactionAnalysis, TransactionInput
from .normalizer import normalize
from .rules import match_rule
from .thresholds import DEFAULT_THRESHOLDS, Thresholds

# What this pipeline actually does today, versus the full spec:
#
#   IMPLEMENTED:     normalization -> rules (Tier 1) -> fuzzy match (Tier 2)
#   NOT IMPLEMENTED: ML classifier (Tier 3, scikit-learn/TF-IDF),
#                     semantic similarity (sentence-transformers),
#                     entity extraction (GLiNER),
#                     persisted merchant memory / feedback table,
#                     deterministic accounting validation (date/balance/
#                       duplicate checks -- note the parser's own
#                       balance-chain check already exists separately
#                       and is untouched by this module),
#                     API endpoints,
#                     wiring into the extraction endpoint.
#
# This is deliberate, not an oversight: per this project's incremental
# rule, this is the smallest real first piece (the two cheapest,
# fastest, dependency-light tiers), built and tested standalone before
# adding heavier ML/embedding tiers or touching production extraction
# code. See HANDOFF for what's proposed next.
#
# Because of this, `decision` here is necessarily more conservative than
# the full system will eventually be: anything neither tier is confident
# about goes to REVIEW. That's correct for this stage -- a transaction
# should never be auto-accepted by a tier that doesn't exist yet.


def analyze_transaction(
    item: TransactionInput,
    candidates: list[str],
    thresholds: Thresholds = DEFAULT_THRESHOLDS,
) -> TransactionAnalysis:
    normalized = normalize(item.description)

    rule_result = match_rule(normalized)
    if rule_result is not None:
        label, confidence = rule_result
        return TransactionAnalysis(
            original_description=item.description,
            normalized_description=normalized,
            method=Method.RULE,
            rule_label=label,
            rule_confidence=confidence,
            decision=Decision.ACCEPT,
        )

    fuzzy_result = best_match(normalized, candidates)
    if fuzzy_result is not None:
        matched_text, similarity = fuzzy_result
        if similarity >= thresholds.fuzzy_accept_threshold:
            return TransactionAnalysis(
                original_description=item.description,
                normalized_description=normalized,
                method=Method.FUZZY_MATCH,
                fuzzy_match_text=matched_text,
                fuzzy_similarity=similarity,
                decision=Decision.ACCEPT,
            )
        if similarity >= thresholds.fuzzy_floor:
            # Worth surfacing as a hint to the reviewer, but not strong
            # enough alone to accept -- record it and still send to review.
            return TransactionAnalysis(
                original_description=item.description,
                normalized_description=normalized,
                method=Method.FUZZY_MATCH,
                fuzzy_match_text=matched_text,
                fuzzy_similarity=similarity,
                decision=Decision.REVIEW,
                review_reasons=["fuzzy match below accept threshold"],
            )

    return TransactionAnalysis(
        original_description=item.description,
        normalized_description=normalized,
        method=Method.NONE,
        decision=Decision.REVIEW,
        review_reasons=["no rule or fuzzy match; classifier/semantic tiers not yet implemented"],
    )


def analyze_transactions(
    items: list[TransactionInput],
    thresholds: Thresholds = DEFAULT_THRESHOLDS,
) -> list[TransactionAnalysis]:
    """Batch entry point (spec section 27): processes a whole statement's
    transactions together so later ones can fuzzy-match against earlier
    ones in the same batch -- recognizing a repeated merchant within one
    statement even before any cross-statement merchant memory exists.
    """
    results: list[TransactionAnalysis] = []
    seen_normalized: list[str] = []
    for item in items:
        analysis = analyze_transaction(item, candidates=list(seen_normalized), thresholds=thresholds)
        results.append(analysis)
        seen_normalized.append(analysis.normalized_description)
    return results


__all__ = ["analyze_transaction", "analyze_transactions"]
