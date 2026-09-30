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

1. **Phase 1 — Converter (built, in review).** Bank statement PDF ->
   clean Excel, with a running-balance sanity check on every row. Global
   bank coverage. Any row whose balance can't be confirmed against the
   printed statement is flagged `needs_review` for a human — never
   silently trusted. A self-hosted NLP layer (see `backend/nlp/`) is
   being added on top to cut manual review volume, without ever touching
   that guarantee.
2. **Phase 2 — Categorization (not started).** Bank statements + cash
   books -> transactions classified into Main Heads and Sub Heads.
   Deliberately not started: the real classification conventions aren't
   known until Phase 1 has real usage. `statement_notes` and
   `demand_signals` exist today to capture that signal — read-and-store
   only, nothing automatic yet.
3. **Phase 3 — Trial Balance & Financial Statements (not started).**
   Categorized data -> Trial Balance -> current-period financial
   statements, using the prior period's financials as the baseline.
4. **The assistant layer (not started, not architected).** A chat/
   assistant that proposes classification or parsing improvements for a
   human to approve — never applies anything automatically.

The order isn't up for renegotiation just because the destination is
ambitious: each later phase depends on real data from the phase before
it, not a guess.

## Pricing tiers

| Tier | Status | What's in it |
|---|---|---|
| **Free** | Live | Conversion, all bank profiles incl. AI fallback, 3 conversions/month, notes. |
| **Basic** | Spec'd, not billed | Higher/unlimited conversions, priority processing. Price/cap not yet set; Stripe gated behind a working, deployed frontend. |
| **Premium** | Vision only | Phase 2 and 3: categorization, Trial Balance, financial statements, the assistant layer. |

## Explicitly out of scope right now

Reconciliation against external records, a categorization UI, financial
statement generation, teams/multi-user accounts, any Stripe work beyond
Basic, any automatic classification that isn't human-reviewed first.

## Current known gaps

- No privacy policy naming the specific third-party AI provider (a
  general "AI-assisted processing" disclosure exists in `frontend/app/privacy/page.tsx`).
- Exact Basic-tier price and conversion cap not yet set.
- NLP layer is at Slice 1 (normalization + rules + fuzzy matching) —
  classifier, semantic-similarity, and entity-extraction tiers not built.
