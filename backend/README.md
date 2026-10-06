# FastAPI backend

The backend for Vellotalley, a global bank-statement-to-Excel converter
for bookkeepers, with a self-hosted NLP transaction-intelligence layer
(`nlp/`) and a three-tier extraction system (bank profile -> local
header/statistical heuristic -> optional LLM fallback). Column mapping in
the heuristic tier is implemented in code and does not require a remote AI
provider. The frontend lives in `../frontend/` (Next.js). See
`../ARCHITECTURE.md` for the full picture and `../PRODUCT.md` for the
product vision -- this file only covers running the backend itself.

## Before running

1. Apply `database/0003_add_transaction_sequence.sql` to the existing Supabase project. This preserves exact printed ordering when multiple entries have the same date.
2. In Supabase Storage, create a **private** bucket called `statements` (or set `STATEMENT_BUCKET`). The backend uses its service-role key only on the server to store PDFs under `<user-id>/<statement-id>/source.pdf`.
3. Copy `.env.example` to `.env` and set `SUPABASE_URL` and `SUPABASE_SERVICE_ROLE_KEY`. Never expose the service-role key to a browser or commit it.
4. Install dependencies:

```powershell
python -m pip install -r requirements.txt
```

4. Run:

```powershell
uvicorn app.main:app_factory --factory --reload
```

## API flow

All endpoints require `Authorization: Bearer <Supabase access token>`.

1. `POST /v1/statements` (multipart: `client_id`, `bank_profile`, `file`) validates the profile/PDF/client ownership, enforces the configured current-month conversion limit (except for server-configured IDs in `FREE_UNLIMITED_USER_IDS`), uploads the source PDF, and creates a processing statement.
2. `POST /v1/statements/{statement_id}/extract` downloads the source PDF, parses it, saves transactions, marks completion, and returns the preview JSON.
3. `GET /v1/statements` lists only the current user's statements.
4. `GET /v1/statements/{statement_id}/excel` regenerates and downloads the workbook after verifying ownership.

The backend never accepts `user_id` from the client. It verifies the bearer token then applies user ownership filters in every access to clients and statements. Monetary values are converted through `Decimal(str(value))` before insertion into `numeric(14,2)` columns.

## Still required before live use

- Create the private storage bucket above and test against the real Supabase project.
- Add integration tests with real test users/tokens, all three supplied PDFs, non-PDF upload, unsupported profile, and cross-user statement access.
- Decide where to host the backend. Do not start Next.js or Stripe until this backend milestone is approved.
