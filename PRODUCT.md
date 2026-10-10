# PRODUCT.md — Vellotalley

## What this is

Vellotalley converts bank-statement PDFs into clean, reviewable Excel
files for bookkeepers and small accounting firms — and is the first step
of a larger plan to eventually take a client's raw financial documents
all the way to finished financial statements.

## Who it's for

Bookkeepers and small accounting firms who currently do this by hand:
opening a client's bank statement PDF, manually re-typing transactions
into a spreadsheet, and checking the running balance themselves.
Vellotalley does the extraction and the balance-chain verification; the
human still reviews anything flagged.

## The full vision, in order

1. **Phase 1 — Bank statement converter.** Convert a bank-statement PDF
   into clean, reviewable Excel. This phase is only the converter; it does
   not categorize cash books or prepare a Trial Balance or financial
   statements. Extraction rows remain subject to the unconditional
   `needs_review` rule.
2. **Phase 2 — Raw-data categorization.** Read raw cash books and other
   supporting data, then organize recurring transactions consistently
   into Main Heads and Sub Heads. Use prior-year Trial Balances and
   financial statements as evidence for the organization's accounting
   basis, prior heads, balances, and treatment patterns. Ask focused
   questions when reference data is missing. Begin with proposed
   general-purpose Main Heads and Sub Heads derived from the accounting
   data provided by the owner; treat them as a starting taxonomy, not as
   a universal chart that overrides an organization's own prior-year
   records. Keep suggestions reviewable and traceable to source records;
   the result should be clean, pivot-ready categorized data that can feed
   a Trial Balance.
3. **Phase 3 — Trial Balance and financial statements.** Build a Trial
   Balance from reviewed Phase 2 data. Ask the user for prior-year
   financial statements or the missing information needed to complete
   the work. Let the user review unresolved items and outputs, then
   generate approved financial statements in Excel and PDF.

The phases are distinct and sequential. Phase 1 is the converter; Phase 2
is raw bookkeeping data categorization; Phase 3 is Trial Balance and
financial-statement preparation. Existing standalone parsers, schema, or
utilities for later phases are foundations, not proof those workflows are
available in the website.

## Phase 2/3 question bank

Questions should be conditional: inspect uploaded records first, ask only
for information that is missing or genuinely ambiguous, explain why it is
needed, and let the user mark an answer unknown when it is safe to defer.
These are candidate questions for an accountant-reviewed questionnaire,
not a script to ask every user every question:

- What organization, financial year, reporting period, and currency do
  these source files belong to?
- Is the organization using cash or accrual accounting? Can a prior-year
  Trial Balance or financial statements confirm the basis?
- Should the Main Heads and Sub Heads from last year be reused, revised,
  or mapped to the proposed general-purpose heads?
- Which bank accounts, cash books, units, branches, or departments are
  represented, and should recurring dimensions be kept in separate
  columns?
- Are source schedules available for payroll, fees, receivables, taxes,
  or other entries that cannot safely be derived from a cash book alone?
- Which recurring transactions need clarification, and what source
  evidence supports their accounting treatment?
- For Phase 3, what opening balances and prior-year financial statements
  should carry forward, and what required balances or disclosures are
  still missing?
- Which financial statements and comparative periods does the user need?

The questionnaire and any accounting rules it expresses require owner and
accounting review before they are used to generate financial outputs.

## Pricing tiers

| Tier | Status | What's in it |
|---|---|---|
| **Free** | Built, not deployed | Conversion, all bank profiles incl. AI fallback, 3 conversions/month, notes. |
| **Basic** | Spec'd, not billed | Higher/unlimited conversions, priority processing. Price/cap not yet set; Stripe gated behind a working, deployed frontend. |
| **Premium** | Vision only | Future Phase 2 categorization and Phase 3 Trial Balance/financial-statement workflows. |

## Explicitly out of scope right now

Teams/multi-user accounts, any Stripe work beyond Basic, and any
automatic classification or financial output that is not human-reviewed.

## Current known gaps

- Production deployment and its provider retention/analytics settings
  have not been verified. The in-app privacy page documents the configurable
  LLM fallback, service providers, data categories, and account deletion,
  but has not had jurisdiction-specific legal review.
- Exact Basic-tier price and conversion cap not yet set.
- NLP layer is at Slice 1 (normalization + rules + fuzzy matching) —
  classifier, semantic-similarity, and entity-extraction tiers not built.
- Phase 2 and Phase 3 are the product direction above, but their complete
  end-user workflows are not yet implemented.
- Proposed general-purpose account heads are derived from owner-provided
  source data and remain a proposal until reviewed and approved; a blank
  live reference table is not evidence that those heads are deployed.
