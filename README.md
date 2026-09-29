# VELLOTALLEY

VELLOTALLEY is a bank-statement conversion workflow for Pakistani financial statements. It accepts PDF statements, extracts transactions using bank-specific profiles and fallback parsing, validates balances, and exports a clean workbook for reconciliation.

## Repository layout

```
.
├── CONVERTER_COMPLETE_FIXED/    FastAPI backend and Python parsing logic
├── frontend/                    Next.js app for authentication and dashboard
├── .github/workflows/           CI/CD pipelines
├── Makefile                     Common local development tasks
├── .env.example                 Environment template (shared)
└── README.md                    This file
```

## Quick start

### Prerequisites

- Python 3.12+
- Node.js 20+
- A Supabase project with:
  - Auth enabled
  - `statements`, `clients`, `transactions`, `statement_notes`, and `demand_signals` tables created
  - A private storage bucket named `statements` (or configure `STATEMENT_BUCKET`)

### One-command setup

```bash
make install-backend install-frontend
cp .env.example .env
# Edit .env with your Supabase credentials
cp frontend/.env.example frontend/.env.local
```

### Run locally

```bash
# Terminal 1: Backend (runs on http://localhost:8000)
cd CONVERTER_COMPLETE_FIXED
uvicorn app.main:app_factory --factory --reload

# Terminal 2: Frontend (runs on http://localhost:3000)
cd frontend
npm run dev
```

### Run tests

```bash
make test              # Run both backend and frontend tests
make backend-test     # Python tests only
make frontend-test    # Lint and build check
```

## Required environment variables

### Backend (CONVERTER_COMPLETE_FIXED/.env)

```bash
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_SERVICE_ROLE_KEY=eyJhbGc... # Service role key from Supabase settings
STATEMENT_BUCKET=statements           # Storage bucket name
FREE_MONTHLY_LIMIT=3                  # Conversions per calendar month
ANTHROPIC_API_KEY=sk-ant-...          # Optional: for AI extraction fallback
```

### Frontend (frontend/.env.local)

```bash
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000
NEXT_PUBLIC_APP_NAME=VELLOTALLEY
```

## API Overview

All endpoints require `Authorization: Bearer <supabase-access-token>`.

### Clients
- `POST /v1/clients` — Create a new client
- `GET /v1/clients` — List your clients

### Statements
- `POST /v1/statements` — Upload a bank statement PDF
- `GET /v1/statements` — List your statements
- `GET /v1/statements/{id}` — Get statement details
- `POST /v1/statements/{id}/extract` — Parse the PDF (transition from processing → completed or failed)
- `POST /v1/statements/{id}/retry` — Retry a failed extraction
- `GET /v1/statements/{id}/transactions` — Get parsed transactions
- `GET /v1/statements/{id}/excel` — Download as Excel workbook
- `POST /v1/statements/{id}/notes` — Add a review note
- `GET /v1/statements/{id}/notes` — List review notes

### Health
- `GET /healthz` — API health check

## Parsing flow

1. **Upload** → PDF stored in Supabase Storage, statement record created with status=`processing`
2. **Extract** → Runs one of three parsers:
   - **Profile**: Bank-specific coordinate-based extraction (fastest, most reliable)
   - **Heuristic**: Layout-based fallback (handles new banks, lower confidence)
   - **LLM**: Claude-based extraction (when heuristic confidence < 85%)
3. **Validate** → Each transaction checked: `prev_balance - debit + credit = new_balance`
4. **Flag** → Rows that don't reconcile marked `needs_review: true`
5. **Export** → Excel workbook with flagged rows highlighted

## Testing

### Backend

Run all Python tests:
```bash
cd CONVERTER_COMPLETE_FIXED
pytest
```

Tests are split by module:
- `test_intl_parsing.py` — International statement parsing (IBAN, date normalization, FX)
- `test_ocr_extraction.py` — OCR fallback pipeline

To add new tests, place them in `CONVERTER_COMPLETE_FIXED/test_*.py`.

### Frontend

Lint and build check:
```bash
cd frontend
npm run lint
npm run build
```

## CI/CD

GitHub Actions runs on every push and pull request:

- **Backend**: Python 3.12, installs dependencies, runs `pytest`
- **Frontend**: Node 20, lints TypeScript/JSX, builds Next.js app

Check `.github/workflows/ci.yml` for the full pipeline.

## Deployment

### Backend

The backend is a FastAPI app that can be deployed to:
- Heroku (with Procfile)
- Railway
- Fly.io
- DigitalOcean App Platform
- Any cloud that supports Python + uvicorn

**Key settings:**
- Set `SUPABASE_URL`, `SUPABASE_SERVICE_ROLE_KEY` as environment variables
- Expose port 8000 (or configure via `PORT` env var)
- For production, use a real ASGI server (not `--reload`)

### Frontend

The frontend is a Next.js 16 app that deploys to:
- Vercel (recommended)
- Netlify
- Any Node.js hosting

**Key settings:**
- Set `NEXT_PUBLIC_API_BASE_URL` to your backend URL
- Run `npm run build` then `npm start`

## Architecture notes

### Security

- The backend uses Supabase service-role key **server-side only**. Never expose it to the browser.
- Every API endpoint checks user ownership via bearer token validation.
- PDFs are stored in a private Supabase Storage bucket.
- Row-level security (RLS) policies provide a second line of defense on the database.

### Parsing strategy

- Bank profiles live in `statement_converter.py` and define column positions for each bank.
- Heuristic parser uses OCR + pattern matching for unlisted banks.
- LLM parser is a fallback when heuristic confidence is low.
- All transactions are validated against the printed running balance.
- Uncertain rows are flagged, not silently accepted.

### Storage

- PDFs are stored under `{user_id}/{statement_id}/source.pdf` in Supabase Storage.
- Transaction data is normalized: dates, amounts stored as ISO strings and decimals.
- Statement notes provide a human-readable audit trail.

## Troubleshooting

### Backend won't start

- Check `SUPABASE_URL` and `SUPABASE_SERVICE_ROLE_KEY` are set.
- Verify Supabase project is active and accessible.
- Run `uvicorn app.main:app_factory --factory --reload --log-level=debug` for details.

### Parsing fails

- Check the bank profile is supported (or use `auto` for AI fallback).
- Verify the PDF is a valid bank statement, not a corrupted or scanned image.
- Check Supabase Storage bucket exists and is private.
- If using `auto`, ensure `ANTHROPIC_API_KEY` is set for LLM fallback.

### Frontend can't reach backend

- Verify `NEXT_PUBLIC_API_BASE_URL` is correct (e.g., `http://localhost:8000` for dev).
- Check backend is running and accessible.
- Look for CORS errors in browser console.

## Product goals

✓ Parse bank statements reliably  
✓ Highlight uncertain rows instead of guessing  
✓ Support multiple Pakistani banks  
✓ Provide OCR fallback for scanned statements  
✓ Keep review and reconciliation workflows transparent  
✓ Export clean, auditable Excel workbooks  

## Contributing

1. Create a branch: `git checkout -b feat/your-feature`
2. Make changes and test: `make test`
3. Commit and push
4. Open a pull request against `main`

CI will automatically validate your changes.
