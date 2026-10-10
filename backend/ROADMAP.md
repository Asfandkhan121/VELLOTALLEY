# Product roadmap

Vellotalley has three distinct product phases. This file describes the
intended data-processing responsibilities; it does not claim that a phase
is complete merely because a parser, table, or isolated utility exists.

## Phase 1 — Bank statement converter

Convert a bank-statement PDF into clean, reviewable Excel. Phase 1 is only
the converter. It does not categorize raw cash books, prepare a Trial
Balance, or generate financial statements.

## Phase 2 — Raw bookkeeping data categorization

Read raw cash books and supporting accounting data. Use prior-year Trial
Balances and financial statements as evidence for the organization's
accounting basis, existing Main Heads/Sub Heads, opening balances, and
recurring transaction treatment. When useful reference data is missing,
ask focused questions instead of assuming.

Start with proposed general-purpose Main Heads and Sub Heads derived from
owner-provided accounting data, then use each organization's prior-year
heads and evidence to refine the mapping. These defaults do not replace a
client's actual chart of accounts. Propose consistent heads for recurring
transactions.
Preserve source provenance, keep suggestions reviewable, and produce clean,
pivot-ready categorized data for Phase 3. Do not infer accruals, payroll
expense, earned income, opening balances, or journal entries from cash-book
descriptions alone when their supporting evidence is unavailable.

## Phase 3 — Trial Balance and financial statements

Build a Trial Balance from reviewed categorized data. Ask for prior-year
financial statements or the information needed to complete the requested
statements. Show unresolved data and calculations for review, then export
approved financial statements to Excel and PDF.

The Phase 2/3 question bank asks only about missing or ambiguous
information. Candidate topics include entity and period, currency,
cash/accrual basis, prior-year head mapping, represented sources and
dimensions, supporting payroll/fee/receivable schedules, opening
balances, prior-year financials, missing disclosures, and requested
statements/comparatives. Accounting review is required before questions
are treated as rules for financial outputs.

## Accounting invariants

- Extraction review status, extraction confidence, and categorization
  evidence are separate concepts.
- `needs_review = true` remains unconditional for heuristic and LLM
  extracted transactions.
- User corrections and approvals must be explicit and traceable.
- No classification or financial output is silently treated as verified.
- `statement_notes` and `demand_signals` remain read-and-store only.
