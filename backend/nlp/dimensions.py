"""Suggest recurring-entity columns ("dimensions", e.g. branch/campus) from narrations.

Nothing here is hard-coded to a word: for each narration, blank out one token at a
time; when the same surrounding phrase recurs with >=3 different tokens in the
blank, that blank is a "slot". Slots sharing values merge into one dimension, so
"campus 9" and "c 9" become one column without anyone saying they mean the same.

Suggestions only. This is separate from transactions.needs_review (always true for
heuristic/LLM rows) and statements.confidence; nothing reads these results back
into parsing or classification. Local, deterministic, no external AI.
"""
from __future__ import annotations

import itertools
import re
from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import date

_TOKEN = re.compile(r"[a-z]+|\d+")

MIN_VALUES = 3        # distinct tokens in the blank
MIN_ROWS = 5          # rows backing a slot
MIN_CONTEXT = 2       # tokens of surrounding phrase required
MIN_REPEAT = 2.0      # rows per value; below this values are ids (cheque numbers)
MAX_ID_DIGITS = 6     # digit values this long are ids, not entities
MERGE_JACCARD = 0.3   # value overlap that merges two slots into one dimension
PERIOD_PURITY = 0.8   # value maps to one calendar month => it is time, not an entity


@dataclass(frozen=True)
class Dimension:
    values: dict[str, int]          # value -> rows
    rows: int
    phrases: tuple[str, ...]        # example contexts, '*' marks the blank


def _tokens(text: object) -> list[str]:
    return _TOKEN.findall(str(text).lower())


def _slots(narrations: list[str]) -> dict[tuple[str, ...], Counter]:
    groups: dict[tuple[str, ...], Counter] = defaultdict(Counter)
    for text in narrations:
        words = _tokens(text)
        if len(words) - 1 < MIN_CONTEXT:
            continue
        for i, word in enumerate(words):
            groups[(*words[:i], "*", *words[i + 1:])][word] += 1
    return {k: v for k, v in groups.items()
            if len(v) >= MIN_VALUES and sum(v.values()) >= MIN_ROWS}


def _is_period(months_by_value: dict[str, Counter]) -> bool:
    total = sum(sum(c.values()) for c in months_by_value.values())
    top = sum(c.most_common(1)[0][1] for c in months_by_value.values())
    return total > 0 and top / total >= PERIOD_PURITY


def discover_dimensions(narrations: list[str], dates: list[date] | None = None) -> list[Dimension]:
    """Return suggested dimensions, biggest first. `dates` (parallel to narrations)
    lets month-like slots ("M/O Jan-25") be recognised as periods and dropped."""
    slots = _slots(narrations)
    keys = list(slots)
    parent = list(range(len(keys)))

    def find(x: int) -> int:
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    for a, b in itertools.combinations(range(len(keys)), 2):
        va, vb = set(slots[keys[a]]), set(slots[keys[b]])
        if len(va & vb) / len(va | vb) >= MERGE_JACCARD:
            parent[find(a)] = find(b)

    clusters: dict[int, list[int]] = defaultdict(list)
    for i in range(len(keys)):
        clusters[find(i)].append(i)

    found: list[Dimension] = []
    for ids in clusters.values():
        values: Counter = Counter()
        for i in ids:
            values.update(slots[keys[i]])
        if sum(values.values()) / len(values) < MIN_REPEAT:
            continue
        if any(v.isdigit() and len(v) >= MAX_ID_DIGITS for v in values):
            continue
        ctxs = {keys[i] for i in ids}
        if dates is not None:
            months: dict[str, Counter] = defaultdict(Counter)
            for text, when in zip(narrations, dates):
                words = _tokens(text)
                for i, word in enumerate(words):
                    if word in values and (*words[:i], "*", *words[i + 1:]) in ctxs:
                        months[word][when.month] += 1
                        break
            if months and _is_period(months):
                continue
        top = sorted(ids, key=lambda i: -sum(slots[keys[i]].values()))[:3]
        found.append(Dimension(dict(values), sum(values.values()),
                               tuple(" ".join(keys[i]) for i in top)))
    return sorted(found, key=lambda d: -d.rows)
