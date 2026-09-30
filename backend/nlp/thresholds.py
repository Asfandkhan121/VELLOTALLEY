from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Thresholds:
    """Every number here is a policy decision, not a magic constant
    buried in pipeline logic. Change these to tune the automatic-accept
    rate without touching any tier's code."""

    # Fuzzy match (RapidFuzz token_sort_ratio, 0-100) above which a match
    # to a known/previously-approved description is trusted enough to
    # accept without further tiers.
    fuzzy_accept_threshold: float = 92.0
    # Below this, don't even surface the fuzzy match as a hint -- too
    # weak to be useful signal either way.
    fuzzy_floor: float = 60.0


DEFAULT_THRESHOLDS = Thresholds()
