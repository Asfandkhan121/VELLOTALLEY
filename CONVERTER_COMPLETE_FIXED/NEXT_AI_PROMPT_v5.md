# Copy-ready prompt for the next AI agent

```text
You are continuing the Pakistani Bank Statement Converter project. Read this
prompt completely, inspect the attached/current project files, and work
incrementally. At the end of every milestone, you MUST create both:

1. A detailed handoff file.
2. A copy-ready prompt for the next AI explaining the plan, completed work,
   current work, remaining work, files, tests, and blockers.

## Project goal

Build a micro-SaaS for Pakistani bookkeepers and small accounting firms. It
converts bank-statement PDFs into clean, reviewable Excel files.

## Non-negotiable rules

- Build one milestone at a time. Do not scaffold the full web application at once.
- Do not start Next.js or Stripe until the FastAPI backend is fully tested and
  approved by a human.
- Preserve the existing parser and Excel exporter. Do not rewrite them without a
  specific reproduced defect.
- Pakistani dates are day-first, never assume US month-first dates.
- Keep parsing bank-profile-based, not hardcoded to one bank.
- Never import statement headers, footers, totals, account information, branch
  information, page labels, or legal notices as transactions.
- Balance rule: new_balance = previous_balance - debit + credit.
- Missing or inferred balances must remain needs_review = true.
- Enforce ownership server-side; never trust a client-provided user_id.
- Never expose a Supabase service-role key to a browser/frontend.
- Handle monetary values as exact decimals, not floats, in database persistence.

## Work completed

### 1. PDF parser - implementation complete; not re-verified this session

- `statement_converter.py` contains `parse_statement(pdf_path, bank_profile)`.
- Supported banks: MCB (`mcb`), Samba (`samba`), and First Women Bank (`fwb`).
- Output fields: date, description, debit, credit, balance, needs_review.
- Previously verified (prior milestone, not re-run in the v5 session because no
  sample PDFs were available): MCB 18/0 flagged, Samba 625/0, FWB 4/2 (source
  statement genuinely omits two printed balances).
- **No sample PDFs have been supplied in the last two handoffs.** If you still
  don't have MCB/Samba/FWB sample PDFs, ask for them before claiming the parser
  is re-verified — do not assume it still works untested.

### 2. Excel export - complete and verified

- `excel_export.py` contains `export_to_excel(transactions, output_path)`.
- Styled/frozen header, real Excel day-first dates, formatted money columns,
  amber review rows, column widths, Debit/Credit formula totals.
- Re-verified indirectly in v5: a generated workbook from the API test harness
  had correct row order, correct content-type, and non-trivial byte size.

### 3. Supabase database - schema, migration, and bucket all live and verified

Project: `xujijonwxxoxxtvhorfi` (reachable via this environment's Supabase tool
integration in the v5 session; confirm it's still the intended project before
reusing it).

- `clients`, `statements`, `transactions` tables exist with RLS enabled, owner-
  scoped policies (`auth.uid() = user_id`, and a subquery on `statements` for
  `transactions`), a composite client/user ownership FK
  (`statements_client_owner_fkey`), and `numeric(14,2)`-precision money columns.
- **`database/0003_add_transaction_sequence.sql` is now APPLIED** (done in v5).
  `transactions.transaction_sequence` (int, not null) and the unique index
  `transactions_statement_sequence_idx (statement_id, transaction_sequence)` exist.
- **Private Storage bucket `statements` now EXISTS** (created in v5,
  `public = false`). No policy changes were made to `storage.objects` — the
  backend only ever accesses it through the service-role key, which bypasses RLS.
- **Cascading delete verified live** in v5: deleting a `statements` row deletes
  its `transactions` rows (`confdeltype = 'c'` on `transactions_statement_id_fkey`).
  Tested with 3 transactions (including two sharing a date, exercising the new
  sequence unique index): before=3, after=0. Test data was fully cleaned up.
- Minor, non-blocking advisor findings from v5 (see HANDOFF_v5.md for detail):
  a `rls_auto_enable()` SECURITY DEFINER function that looks like platform
  scaffolding rather than app code, and 3 RLS policies that could be optimized
  with `(select auth.uid())` instead of `auth.uid()` for per-row re-evaluation.

### 4. FastAPI backend - endpoint logic validated; live HTTP-over-network still pending

Files: `app/main.py`, `app/repository.py`, `app/config.py`,
`database/0003_add_transaction_sequence.sql` (now applied),
`.env.example`, `requirements.txt`, `README.md`.

Endpoints:
- POST `/v1/statements` - authenticated PDF upload; validates bank profile, PDF
  signature, client ownership, 3-conversions-per-calendar-month free limit.
- POST `/v1/statements/{statement_id}/extract` - parses, persists transactions,
  marks completed, returns preview JSON.
- GET `/v1/statements` - lists only the authenticated user's statements.
- GET `/v1/statements/{statement_id}/excel` - ownership-checked, rebuilds the
  workbook in printed order, downloads it (also serves re-download).

**v5 session validated all of this against the real endpoint code** (not a
rewrite, not a mock of the routes themselves) using FastAPI's `TestClient` with
`create_app(settings=, repository=)`'s existing dependency-injection seam and an
in-memory fake repository implementing the exact same method contract as
`SupabaseRepository`. 24/24 checks passed: 401 (missing/invalid token), 422 (bad
profile), 415 (non-PDF filename and non-PDF bytes with `.pdf` extension), 404
(unowned client, cross-user statement access, unknown statement id), 429 (4th
monthly upload), 409 (re-extract completed statement, excel download with no
transactions), correct 2-decimal money serialization, per-user statement list
isolation, correct Excel content-type/size, and same-date `transaction_sequence`
ordering surviving into the generated Excel file's row order. Full detail and the
exact table of checks is in `HANDOFF_v5.md`.

`parse_statement` was stubbed with canned data for this test run, because no
sample PDFs were available — the parser itself was not re-exercised.

Also found in v5: `app/main.py`'s module-level `app = create_app()` (line 121)
constructs a live `SupabaseRepository` at import time, which is correct for
`uvicorn app.main:app --reload` but makes the module hard to import for testing
without a real-shaped Supabase key. Not fixed yet (out of "validate only" scope)
— consider a small lazy-init refactor in a future milestone.

## Current work - do this next

1. **Get the three sample bank-statement PDFs (MCB, Samba, FWB) attached to the
   working files**, and actually run `parse_statement()` on them (not stubbed)
   through the same TestClient-based harness used in v5, to get a true end-to-end
   validation including the real parser.
2. **Do a genuine live-network smoke test** of `uvicorn app.main:app --reload`
   against the real Supabase project, using the actual `SUPABASE_SERVICE_ROLE_KEY`
   (which this sandboxed environment does not have access to) from a machine that
   can reach `*.supabase.co`. Re-run the same 24 checks as real HTTP calls with
   two real Supabase auth users/tokens. This is close to a formality now — DB-side
   correctness (RLS, cascade, ownership FKs, sequence ordering) and endpoint-logic
   correctness are both already proven; this step is about proving the wiring
   between them over a real network with real credentials.
3. Once both of the above are done and pass, **stop and get explicit human
   approval before starting Next.js or Stripe work.**

## What remains after FastAPI approval

1. Next.js frontend: magic-link login, upload page, preview table,
   dashboard/past conversions, Excel download button.
2. Stripe: free tier is 3 conversions/month; $15/month subscription for unlimited
   conversions; Checkout plus webhook to update subscription status.

## Still out of scope

- Reconciliation/matching against ledgers.
- Categorization UI.
- Financial statement generation.
- Multi-currency.
- Team/multi-user accounts.
```
