# Bank Statement Converter - FastAPI Handoff (v4)

## Project

A micro-SaaS for Pakistani bookkeepers that turns bank-statement PDFs into clean, reviewable Excel files. Build incrementally; Next.js and Stripe remain out of scope until FastAPI is fully validated and approved.

## Completed milestones

1. **Parser:** coordinate/profile-driven support for MCB, Samba, and FWB. Verified results: MCB 18/0 flagged, Samba 625/0, FWB 4/2 (the two source rows genuinely omit printed balances).
2. **Excel:** styled workbook, real day-first Excel dates, money formatting, warning rows, and formula totals.
3. **Supabase schema:** clients/statements/transactions, RLS, composite client/user ownership protection. Applied and live-tested according to `HANDOFF_v3.md`.
4. **FastAPI backend:** implemented in `app/`, but not yet executed against a configured Supabase project.

## FastAPI implementation

- `POST /v1/statements`: bearer-authenticated PDF upload; validates PDF/profile/client ownership, applies the 3-per-calendar-month free limit, stores source PDF privately, creates a processing statement.
- `POST /v1/statements/{statement_id}/extract`: downloads PDF server-side, runs existing parser, saves transactions with exact two-decimal text for Postgres `numeric(14,2)`, marks completion, returns preview JSON.
- `GET /v1/statements`: only lists the authenticated user's statements.
- `GET /v1/statements/{statement_id}/excel`: verifies ownership, regenerates a workbook, and downloads it. This endpoint also serves the re-download requirement.

The backend never accepts `user_id` from a client. It verifies the bearer token server-side and explicitly scopes client/statement queries by authenticated user id, even though the server uses a service-role key. The service-role key is backend-only.

## Required follow-up migration

Apply `database/0003_add_transaction_sequence.sql` before running the backend. It adds a stable within-statement transaction order. This is required because date alone cannot preserve printed ordering for several transactions on the same date; UUIDs are not a valid ordering key.

## Before runtime validation

1. Apply the follow-up migration to Supabase.
2. Create a private Supabase Storage bucket named `statements` (or change `STATEMENT_BUCKET`).
3. Set `SUPABASE_URL` and `SUPABASE_SERVICE_ROLE_KEY` as server-side environment variables using `.env.example` as a template. Never put the service-role key in the frontend.
4. Install `requirements.txt` in a normal project virtual environment.
5. Run `uvicorn app.main:app --reload`.

## Required tests before approval

- All three supplied PDFs: MCB, Samba, FWB.
- Unsupported profile returns 422.
- Non-PDF upload returns 415.
- Invalid/missing bearer token returns 401.
- One user cannot list, extract, or download another user's statement ID (404).
- Fourth current-month upload returns 429.
- Verify private storage object creation and re-download Excel order, particularly same-day transactions.

## Do not do yet

Do not start Next.js, Stripe, reconciliation, categorization UI, multi-currency, or team accounts. Stop after FastAPI validation and provide the next detailed handoff.

## Copy-ready prompt for the next AI

```text
Continue the Pakistani Bank Statement Converter project. Read this entire handoff first, then inspect the project files. Work one milestone at a time.

After EVERY milestone, create/update this handoff file and include a copy-ready next-AI prompt inside it. The handoff must state: full plan, completed work, current work, remaining work, file locations, test results, and blockers.

Project goal: a micro-SaaS for Pakistani bookkeepers and small accounting firms that converts bank-statement PDFs into clean, reviewable Excel workbooks.

Rules:
- Do not scaffold the complete web app at once.
- Do not start Next.js or Stripe until FastAPI has been tested and approved.
- Preserve the existing parser and Excel exporter unless there is a specific reproduced bug.
- Dates are day-first; parsing is bank-profile-driven; never import headers/footers/totals/legal text as transactions.
- Validate balances as: new_balance = previous_balance - debit + credit.
- Inferred/missing balances must keep needs_review = true.
- Enforce all ownership checks server-side. Never accept a client user_id and never expose the Supabase service-role key in a browser.
- Use exact decimal money values for database writes.

Completed:
1. PDF parsing is complete for MCB, Samba, and FWB. Results: MCB 18 transactions / 0 flagged; Samba 625 / 0; FWB 4 / 2 (two printed balances are absent, so correctly flagged). The parser's cross-page description-continuation bug is fixed and verified.
2. Excel export is complete: day-first real Excel dates, styled/frozen headers, money formatting, formula totals, and amber review highlighting.
3. The Supabase schema/RLS is applied and live-tested. A required additional migration, database/0003_add_transaction_sequence.sql, must be applied before the backend is used; it preserves printed transaction order when multiple entries share a date.
4. FastAPI implementation is written but not live-validated. Files: app/main.py, app/repository.py, app/config.py, requirements.txt, .env.example, README.md.

Current work - validate FastAPI only:
1. Apply database/0003_add_transaction_sequence.sql.
2. Create a private Supabase Storage bucket named statements (or configure STATEMENT_BUCKET).
3. Set SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY only as server-side environment variables.
4. Install requirements and run uvicorn app.main:app --reload.
5. Test MCB, Samba, and FWB uploads/extractions/Excel downloads.
6. Test invalid token (401), bad profile (422), non-PDF (415), cross-user access (404), fourth monthly upload (429), same-day ordering, and cascade deletion if still untested.
7. Stop and provide concrete results for approval.

Implemented endpoints:
- POST /v1/statements - authenticated upload, profile/PDF/client ownership checks, 3/month free limit.
- POST /v1/statements/{statement_id}/extract - parse, persist, and return preview.
- GET /v1/statements - owned statement list.
- GET /v1/statements/{statement_id}/excel - owned Excel download/re-download.

Remaining after FastAPI approval: Next.js frontend with Supabase magic-link login, upload/preview/dashboard/download; then Stripe Checkout/webhook for $15/month unlimited usage. Still out of scope: reconciliation, categorization UI, financial statements, multi-currency, and teams.
```
