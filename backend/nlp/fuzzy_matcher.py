from __future__ import annotations

from rapidfuzz import fuzz, process


def best_match(normalized_description: str, candidates: list[str]) -> tuple[str, float] | None:
    """Find the closest match to `normalized_description` among
    `candidates`, using RapidFuzz's token_sort_ratio (robust to word
    order and minor punctuation differences -- exactly the "METRO CASH
    CARRY" vs "METRO C&C" case from spec section 12).

    `candidates` is caller-supplied on purpose: this tier doesn't depend
    on the persisted merchant-memory table from spec section 17 (not
    built yet -- see the pipeline module docstring). Today it's useful
    even without persistence: a caller can pass in every other
    already-normalized description from the SAME statement, so a
    merchant appearing multiple times in one statement gets recognized
    against itself. Wiring in a real cross-statement merchant-memory
    table is a deliberate next step, not this one.

    Returns (matched_candidate, similarity_0_to_100) for the best match,
    or None if `candidates` is empty. Does NOT apply any accept/review
    threshold itself -- that policy decision lives in thresholds.py and
    is applied by the pipeline, not buried here.
    """
    if not candidates:
        return None
    result = process.extractOne(normalized_description, candidates, scorer=fuzz.token_sort_ratio)
    if result is None:
        return None
    matched_text, score, _ = result
    return matched_text, score


__all__ = ["best_match"]
