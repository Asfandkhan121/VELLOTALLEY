# Bank Statement Converter handoff v9

## Milestone in progress: secure FastAPI live validation

The bilingual/RTL parser expansion is deferred. The next mandatory checkpoint is to validate the already-built FastAPI service against the real Supabase project without exposing backend credentials.

## What changed in v9

- Refactored `app/main.py` so the application is constructed through `app_factory()` rather than at module import. This lets tests import `create_app()` and use an in-memory repository without supplying any Supabase secret.
- Updated run command: `uvicorn app.main:app_factory --factory --reload`.
- Added `LIVE_VALIDATION.md`, a secure checklist for a human-run test on a controlled machine.
- Included the v8 Ping An parser update in this package.
- Python syntax compilation passed for parser, exporter, FastAPI config, repository, and routes.

## What has already been completed

- Parser profiles: MCB, Samba, FWB, UBL, BOP, Allied, Wio, ADIB, AAIB, Maerki OCR, and Ping An.
- Excel exports with real dates, numeric formatting, warnings, and totals.
- Supabase schema/RLS/ownership tests, private Storage bucket, and stable transaction ordering migration.
- FastAPI endpoint routing and in-memory dependency-injection tests from the earlier v5 validation.

## Do now

Run `LIVE_VALIDATION.md` privately on a machine that can reach Supabase and stores `SUPABASE_URL` plus the backend-only secret locally. Test real supported PDFs, two test users, uploads, extraction, list, Excel download, access isolation, validation errors, monthly limit, and transaction order.

Do not paste service-role/secret keys into a chat, ZIP, prompt, source code, or browser. Do not use customer data without authorization.

## Remains after FastAPI approval

1. Next.js frontend (magic-link login, upload/preview, dashboard, download).
2. Stripe Checkout/webhook for the paid unlimited tier.
3. Deferred parser work: bilingual/RTL source samples when available; Zhejiang reverse chronological Chinese parsing; RAKBANK transaction-page calibration; Emirates NBD multi-line assembler.

## Copy-ready prompt for the next AI

```text
Continue the Bank Statement Converter from HANDOFF_v9.md. Create one updated handoff Markdown file with this copy-ready prompt embedded in it after every milestone, then produce a ZIP containing the code and handoff. Do not include .env files, Supabase service-role/secret keys, or customer statements unless explicitly requested.

The bilingual/RTL expansion is deferred. Current priority is secure, real FastAPI-to-Supabase validation. The API code is complete; v9 changed app/main.py to app_factory() so tests can import the module without a real secret. Start locally using:
uvicorn app.main:app_factory --factory --reload

Read LIVE_VALIDATION.md. On a secure machine only, set SUPABASE_URL and the backend-only Supabase key in a private untracked .env. Run the live test with two test users and authorized real samples. Confirm upload, extraction, list, Excel download, 401 invalid/missing auth, 415 non-PDF, 422 unknown profile, 404 cross-user statement, 429 fourth monthly conversion, and same-day order. Never paste the secret in chat.

Stop for explicit approval after live FastAPI validation. Only then start Next.js. Stripe follows frontend approval. Existing parser profiles include MCB, Samba, FWB, UBL, BOP, Allied, Wio, ADIB, AAIB, Maerki OCR, and Ping An. Bilingual/RTL and certain special layouts are deferred.
```
