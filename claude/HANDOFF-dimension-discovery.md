# Handoff: dimension discovery slice (2026-10-10)

Companion to claude/PHASE2-CONVENTIONS.md (read that first; its section 7 covers the head-table PRs #8-#10).

## What changed
- PR #11 `claude/dimension-discovery` (base main, tip 443ac32): `backend/nlp/dimensions.py` + `backend/test_dimensions.py`.
- `discover_dimensions(narrations, dates=None)` suggests recurring-entity columns (e.g. branch/campus) from narration text. No hard-coded words: blank out one token at a time; a phrase recurring with >=3 different tokens in the blank is a slot; slots with overlapping values merge into one dimension (so `c 9` and `campus 9` become one); id-like values (cheque numbers) and month-like periods (needs dates) are dropped.
- Owner requirement behind it (owner's words, 2026-10-09): the code must read the available data and create columns only for what is present; recurring branch names can differ per client.
- Not wired into parsing, endpoints, DB or frontend. needs_review and statements.confidence untouched. Local, no external AI. Independent of PRs #8-#10.

## Verified (run, with evidence)
- Fresh clone of the pushed branch at 443ac32: backend suite 84 passed; PR #11 mergeable_state clean.
- 5 new tests; mutation check: relaxing the id filters (MIN_REPEAT, MAX_ID_DIGITS) makes the cheque-number test fail.
- Local run on the owner's CB_25 cash book (not committed): one dimension, values 1-10, 203 rows. Earlier prototype runs: centralized cash book -> one dimension (campus + c merged); single-unit books (C9, C-II) -> none.

## Reported only / not verified
- Only exercised on a few real files; no other client's data. Thresholds (3 values, 5 rows, 2 rows/value, Jaccard 0.3, 0.8 month purity) are my choices, untuned.
- Exact-phrase matching catches fewer rows than a loose regex (203 vs 249 on CB_25).

## Still open
1. Loosen matching (word-order variants, e.g. "Shell fleet payment campus-5" vs "Campus-5 Shell fleet"); standalone names (e.g. Nasheman) only join if they share a phrase with numbered ones.
2. Column naming (code only sees the surrounding phrase): needs owner confirmation per suggestion; keep it a suggestion UI/flag, never auto-classify.
3. Owner questions on CB_25 heads: is campus a sub-head part or a separate dimension; are "Receivable from against X" and "Receivable from campuses against X" one head; what are the "-Contra" rows under Income; are the 18 repeated same-day rows real. CB_25 unit/entity unknown; no matching GL.
4. Owner review/merge of PRs #8, #9, #10, #11; seed review; migration numbering drift; revoke the pasted GitHub token (all in PHASE2-CONVENTIONS section 5).

## Next-session prompt
"Project: Vellotalley. Read claude/PHASE2-CONVENTIONS.md and claude/HANDOFF-dimension-discovery.md. PR #11 adds nlp/dimensions.py (suggestion-only branch/campus column discovery). Clone fresh, check PR states via REST first. Do not wire it into parsing or load any seed without the owner's go-ahead. Next only with go-ahead: loosen phrase matching (open item 1), then a suggestions endpoint/UI. Hold needs_review=true unconditional."
