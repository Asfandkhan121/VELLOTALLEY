# Copy-ready prompt for the next AI agent

```text
You are continuing the Pakistani Bank Statement Converter project. Read this prompt completely, inspect the attached/current project files, and work incrementally. At the end of every milestone, you MUST create both:

1. A detailed handoff file.
2. A copy-ready prompt for the next AI explaining the plan, completed work, current work, remaining work, files, tests, and blockers.

## Project goal

Build a micro-SaaS for Pakistani bookkeepers and small accounting firms. It converts bank-statement PDFs into clean, reviewable Excel files.

## Non-negotiable rules

- Build one milestone at a time. Do not scaffold the full web application at once.
- Do not start Next.js or Stripe until the FastAPI backend is fully tested and approved.
- Preserve the existing parser and Excel exporter. Do not rewrite them without a specific reproduced defect.
- Pakistani dates are day-first, never assume US month-first dates.
- Keep parsing bank-profile-based, not hardcoded to one bank.
- Never import statement headers, footers, totals, account information, branch information, page labels, or legal notices as transactions.
- Balance rule: new_balance = previous_balance - debit + credit.
- Missing or inferred balances must remain needs_review = true.
- Enforce ownership server-side; never trust a client-provided user_id.
- Never expose a Supabase service-role key to a browser/frontend.
- Handle monetary values as exact decimals, not floats, in database persistence.

## Work completed

### 1. PDF parser - complete and verified

- `statement_converter.py` contains `parse_statement(pdf_path, bank_profile)`.
- It uses pdfplumber word coordinates, row clustering, and declarative bank profiles.
- Supported banks: MCB (`mcb`), Samba (`samba`), and First Women Bank (`fwb`).
- Output fields: date, description, debit, credit, balance, needs_review.
- Cross-page description continuation bug was fixed: continuation text at the start of the next PDF page now stays with its original transaction.
- Verified results:
  - MCB: 18 transactions, 0 flagged.
  - Samba: 625 transactions, 0 flagged.
  - FWB: 4 transactions, 2 flagged because the source statement omits two printed balances.

### 2. Excel export - complete and verified

- `excel_export.py` contains `export_to_excel(transactions, output_path)`.
- The workbook includes a styled/frozen header, real Excel day-first dates, formatted money columns, amber review rows, column widths, and Debit/Credit formula totals.
- All three supplied sample exports were previously verified.

### 3. Supabase database - complete and live-tested

- The original migration creates `clients`, `statements`, and `transactions` with RLS, indexes, exact `numeric(14,2)` money, and future nullable categorization/reconciliation columns.
- It uses a composite client/user ownership foreign key, so a statement cannot attach to another user's client.
- The migration was applied and verified live with two simulated users; ownership/RLS tests passed.
- A required follow-up migration now exists: `database/0003_add_transaction_sequence.sql`.
- Apply this migration before backend use. It adds a stable transaction order inside each statement, preventing same-date transactions from being reordered in preview or Excel re-downloads.

### 4. FastAPI backend - implementation complete, live validation pending

Project location: `statement_converter_fastapi/`

Important files:

- `app/main.py` - API endpoints.
- `app/repository.py` - server-only Supabase access and ownership-scoped queries.
- `app/config.py` - environment configuration.
- `database/0003_add_transaction_sequence.sql` - required migration.
- `.env.example` - server configuration template.
- `requirements.txt` - pinned dependencies.
- `README.md` - run/setup instructions.
- `HANDOFF_v4.md` - current detailed handoff.

Endpoints implemented:

- POST `/v1/statements` - authenticated PDF upload; validates bank profile, PDF signature, client ownership, and the three-conversions-per-calendar-month free limit. Stores the original PDF privately and creates a `processing` statement.
- POST `/v1/statements/{statement_id}/extract` - downloads the uploaded file server-side, calls the existing parser, persists transactions, marks the statement completed, and returns preview JSON.
- GET `/v1/statements` - lists only the authenticated user's statements.
- GET `/v1/statements/{statement_id}/excel` - checks ownership, rebuilds the workbook from persisted transactions in printed order, and downloads it. This also fulfils re-download.

The backend passed Python syntax compilation. Runtime integration tests have NOT been completed yet because the backend has not been configured against the Supabase project in this environment.

## Current work - do this next

Validate the FastAPI milestone before doing any frontend or Stripe work:

1. Apply `database/0003_add_transaction_sequence.sql` to the existing Supabase project.
2. Create a private Supabase Storage bucket named `statements` (or configure another private bucket using `STATEMENT_BUCKET`).
3. Put `SUPABASE_URL` and `SUPABASE_SERVICE_ROLE_KEY` into server-only environment variables. Never commit or expose the service-role key.
4. Create a virtual environment, install the pinned requirements, and start the API with `uvicorn app.main:app --reload`.
5. Test all three PDFs: MCB, Samba, and FWB.
6. Test errors: missing/invalid bearer token (401), unsupported profile (422), non-PDF upload (415), another user's statement ID (404), and fourth monthly upload (429).
7. Confirm same-date transaction order is retained in the preview and downloaded Excel workbook.
8. Add or run a live cascading-delete test if it has not already been run.
9. Stop and report concrete test evidence for approval.

## What remains after FastAPI approval

1. Next.js frontend: magic-link login, upload page, preview table, dashboard/past conversions, and Excel download button.
2. Stripe: free tier is 3 conversions/month; $15/month subscription for unlimited conversions; Checkout plus webhook to update subscription status.

## Still out of scope

- Reconciliation/matching against ledgers.
- Categorization UI.
- Financial statement generation.
- Multi-currency.
- Team/multi-user accounts.
```
