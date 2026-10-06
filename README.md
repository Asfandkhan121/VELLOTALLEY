# VELLOTALLEY

Vellotalley converts bank-statement PDFs into clean, reviewable Excel
files for bookkeepers and small accounting firms. Bank coverage is
global (11 profiles across Pakistan, UAE, Egypt, Switzerland, and China
so far), not limited to one country.

For the full picture, see the docs at the repo root:
- **`PRODUCT.md`** — vision, tiers, phase roadmap
- **`ARCHITECTURE.md`** — full technical detail
- **`ARCHITECTURE-ESSENTIALS.md`** — five-minute version
- **`AGENTS.md`** / **`CLAUDE.md`** — rules for AI agents working in this repo

This file only covers running the project locally.

## Repository layout

```
.
├── backend/     FastAPI app, PDF parsing, the NLP transaction-intelligence layer
├── frontend/    Next.js app (auth, upload, review, download)
└── *.md         Product/architecture docs (see above)
```

## Prerequisites

- Python 3.12+
- Node.js 20+ and `pnpm` (this frontend uses pnpm, not npm — check
  `frontend/package.json`'s `packageManager` field if unsure)
- A Supabase project with Auth enabled, the `clients`/`statements`/
  `transactions`/`statement_notes`/`demand_signals` tables (see
  `backend/database/`), and a private Storage bucket named `statements`

## Setup

```bash
# Backend
cd backend
pip install -r requirements.txt
cp .env.example .env
# edit .env with your Supabase URL and service-role key

# Frontend
cd ../frontend
pnpm install
cp .env.local.example .env.local
# edit .env.local with your Supabase URL and anon key
```

## Run locally

```bash
# Terminal 1 — backend, http://localhost:8000
cd backend
uvicorn app.main:app_factory --factory --reload

# Terminal 2 — frontend, http://localhost:3000
cd frontend
pnpm dev
```

## Run tests

```bash
# Backend (pytest isn't in requirements.txt -- it's not needed to run the
# app, only to test it)
cd backend
pip install pytest
pytest

# Frontend (type-check; there is no separate lint/test script configured yet)
cd frontend
pnpm exec tsc --noEmit
pnpm build
```

There is no CI pipeline or Makefile in this repo yet — the commands above
are what actually exist to run locally.

## API overview

All endpoints require `Authorization: Bearer <supabase-access-token>`.

**Clients**
- `POST /v1/clients` — create a client
- `GET /v1/clients` — list your clients

**Statements**
- `POST /v1/statements` — upload a bank statement PDF
- `GET /v1/statements` — list your statements
- `GET /v1/statements/{id}` — get statement status/detail
- `POST /v1/statements/{id}/extract` — start extraction (async — returns
  `202` immediately; poll `GET /v1/statements/{id}` for status)
- `POST /v1/statements/{id}/retry` — retry a failed extraction
- `GET /v1/statements/{id}/transactions` — the parsed transactions (preview)
- `GET /v1/statements/{id}/excel` — download as an Excel workbook
- `POST /v1/statements/{id}/notes` — add a review note
- `GET /v1/statements/{id}/notes` — list review notes

## Parsing flow

1. **Upload** — PDF stored in Supabase Storage; a `statements` row is
   created with `status="processing"`.
2. **Extract** — runs one of three tiers, in order:
   - **Profile** — bank-specific column-position extraction (fastest,
     most reliable, in `statement_converter.py`)
   - **Heuristic** — locally maps printed column headings and their page
     coordinates (including common Spanish, French, German, Portuguese and
     Arabic labels); uses statistical layout detection when headings are
     absent. Column assignment does not require a remote AI provider.
   - **LLM** — text extraction through any OpenAI-compatible endpoint
     (self-hosted Ollama, or a free-tier hosted API; see `LLM_*` in
     `backend/.env.example`), an optional fallback used when column detection
     fails or a reported running-balance confidence is below 0.85. A missing
     balance column alone does not trigger it. Scanned
     PDFs with no text layer can't be read by this tier. Claude remains
     available as an optional provider (`LLM_PROVIDER=anthropic`)
3. **Validate** — every transaction checked against
   `previous_balance - debit + credit = new_balance`.
4. **Flag** — rows that don't reconcile are marked `needs_review: true`,
   unconditionally, for anything the heuristic or LLM tier produced.
5. **Export** — Excel workbook with flagged rows highlighted.

A separate, self-hosted NLP layer (`backend/nlp/`) returns text-only
transaction hints in extraction and preview responses — see
`ARCHITECTURE.md` for its current status. It never changes
`needs_review` itself.

## Deployment

Nothing is deployed yet. When ready:
- **Backend**: any host that runs Python/ASGI (Render, Railway, Fly.io,
  etc.). Set `SUPABASE_URL` and `SUPABASE_SERVICE_ROLE_KEY` as real
  environment variables, not a committed `.env` file. Run with a real
  ASGI server, not `--reload`.
- **Frontend**: Vercel is the standard choice for Next.js. Set
  `BACKEND_API_URL` to the deployed backend's URL — it's a server-only
  variable, read by the proxy route, never sent to the browser.

## Security notes

- The Supabase service-role key and all LLM provider API keys are
  backend-only. Never put them in frontend code or commit them.
- Every endpoint checks resource ownership server-side against the
  authenticated user's ID from their bearer token — never a
  client-supplied ID.
- The frontend never calls Supabase directly except for auth; all data
  operations go through the backend via a same-origin proxy
  (`frontend/app/api/backend/[...path]/route.ts`), which is also why no
  CORS configuration exists or is needed on the backend.
- PDFs live in a private Storage bucket; only the backend's service-role
  key can read/write it.

## Troubleshooting

- **Backend won't start**: `SUPABASE_URL`/`SUPABASE_SERVICE_ROLE_KEY`
  missing or wrong — `config.py` raises a clear `RuntimeError` naming
  which one.
- **`auto` extraction fails**: inspect the returned parser error and the PDF's
  text layer/layout first. The local column parser does not require an LLM;
  the optional LLM fallback can still fail if `LLM_MODEL` is unset or
  `LLM_BASE_URL` is unreachable. Scanned PDFs need an OCR-capable path.
- **Frontend can't reach the backend**: check `BACKEND_API_URL` in
  `frontend/.env.local` points at a reachable backend.

## Contributing

```bash
git checkout -b feat/your-feature
# make changes, then:
cd backend && pytest
cd ../frontend && pnpm exec tsc --noEmit
```

Open a pull request against `main`. There's no CI enforcing this yet —
run the checks above yourself before opening the PR.
