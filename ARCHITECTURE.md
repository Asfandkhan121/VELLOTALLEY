# ARCHITECTURE.md — Vellotalley

## Stack

- **Backend**: `backend/` — Python / FastAPI. PDF parsing (`pdfplumber`),
  Excel export (`openpyxl`), a three-tier extraction system, and a
  self-hosted NLP transaction-intelligence module (`backend/nlp/`).
- **Database, Auth, file storage**: Supabase (Postgres + Auth + Storage).
  Project ref `xujijonwxxoxxtvhorfi`, region ap-northeast-1.
- **Frontend**: `frontend/` — Next.js, shadcn/ui on `@base-ui/react`
  (not Radix — matters, see Known Issues history below), Tailwind, pnpm.
  This is the single canonical frontend as of this commit; an earlier,
  simpler hand-built Next.js frontend was retired in favor of this one
  (richer feature set: separate statements list/detail/new pages, a
  backend-proxy pattern avoiding CORS, SWR-based polling) — its history
  remains in git if ever needed.
- **Nothing is deployed yet.** Supabase is live; the backend needs a
  Python host (Render/Railway/Fly.io/etc.) and the frontend needs a Node
  host (Vercel is the standard choice for Next.js) before this is
  reachable by a real user.

## Three-tier extraction (backend)

1. **Profile-based** (`backend/statement_converter.py`) — hand-built
   column layouts per bank. Highest confidence. 11 profiles across
   Pakistan, UAE, Egypt, Switzerland, China — 3 Pakistani ones (MCB,
   Samba, FWB) verified against real sample PDFs; the other 8 are not.
2. **Heuristic fallback** (`backend/heuristic_parser.py`) — statistical
   column detection. Every row `needs_review = true`, unconditionally.
3. **LLM fallback** (`backend/llm_parser.py`) — sends the PDF to
   Anthropic's API as a last resort. Same unconditional
   `needs_review = true`. This has real cost and data-sharing implications;
   `frontend/app/privacy/page.tsx` now names Anthropic and describes the
   automatic fallback trigger.

`bank_profile="auto"` walks all three tiers in order.

## NLP transaction-intelligence layer (backend/nlp/) — separate from the above

Answers a different question per transaction: "do we understand this
transaction well enough to skip human review?" — never conflated with
`needs_review` (extraction quality) or `statements.confidence` (PDF-read
quality). No paid/hosted external AI here, ever — this is the self-hosted
layer, distinct from the LLM *parser* fallback above.

Implemented so far (Slice 1): `normalizer.py` (conservative — never
strips dates/amounts/references), `rules.py` (bank-agnostic transaction-
type keywords), `fuzzy_matcher.py` (RapidFuzz), `pipeline.py` (combines
them into ACCEPT/REVIEW with every evidence score kept separate, never
averaged). The extraction response and transaction-preview endpoint run
this pipeline per statement and return a separate `nlp_insight` for each
transaction; the statement detail page shows the text hint separately
from the extraction review flag. Insights are recomputed from stored
descriptions and are not persisted or trained from user data. The NLP
decision never changes `needs_review` or `statements.confidence`. Not yet
built: the scikit-learn classifier, sentence-
transformers semantic similarity, GLiNER entity extraction, a persisted
feedback/merchant-memory table, a learning workflow, or user-provided
feedback UI.

## Data flow

1. `POST /v1/statements` — authenticated upload (client_id, bank_profile,
   PDF). Creates a `statements` row, `status='processing'`.
2. `POST /v1/statements/{id}/extract` — async, `202` immediately; runs
   extraction as a background task, writes `transactions`, updates
   `statements.status`/`extraction_method`/`confidence`.
3. `GET /v1/statements/{id}` — poll for status.
4. `GET /v1/statements/{id}/transactions` — the preview JSON.
5. `GET /v1/statements/{id}/excel` — regenerates/serves the `.xlsx`.
6. `GET /v1/statements` — past-conversions list.
7. `POST /v1/statements/{id}/retry`.
8. `POST`/`GET /v1/statements/{id}/notes`.
9. `DELETE /v1/account` removes the account's Storage objects, demand
   signals, notes, clients and their cascaded statement data, then deletes
   the Supabase Auth user. Storage, database, and Auth do not share a
   transaction, so a failed step is reported as a possible partial deletion
   and must be resolved before retrying.

## Privacy and retention

The privacy page identifies account and statement data, Supabase storage,
the conditional Anthropic PDF-processing path, the Vercel Analytics
integration, and the account-deletion flow. Account closure is exposed in
Settings. Provider backup retention and production analytics settings are
deployment-controlled and must be verified for each live environment.

## Database schema (5 tables, all RLS-enabled)

`clients`, `statements` (composite FK `(client_id, user_id) ->
clients(id, user_id)` — the real ownership guarantee, enforced at the
schema level), `transactions`, `statement_notes` (read-and-store only),
`demand_signals` (RLS enabled, zero policies, intentionally — service-role
only). Migrations `0001` through `0008` (see git history for detail on
each; `0008` fixed RLS performance and revoked an over-exposed internal
Supabase function).

## Security posture

- Ownership checked server-side against the authenticated user's real ID
  on every endpoint — `_owned_statement()` in `backend/app/main.py`,
  confirmed (via AST analysis) to be called from every endpoint that
  touches a specific statement, no exceptions.
- Service-role key and Anthropic API key: backend-only, confirmed absent
  from frontend code.
- Frontend uses a backend-proxy pattern (`frontend/proxy.ts`) — the
  browser calls the Next.js app itself, which re-derives the session and
  forwards to FastAPI with a bearer token. No CORS needed, backend URL
  never reaches the browser.
- Storage: `statements` bucket private, zero direct-access policies —
  service-role only.
- RLS: all policies use `(select auth.uid())`, not bare `auth.uid()`
  (evaluated once per query, not once per row).

## Known issue history worth remembering

The frontend previously had 4 TypeScript errors in
`components/app/app-shell.tsx` from using Radix's `asChild` prop pattern
against `@base-ui/react` components, which use a `render={<Element/>}`
prop instead — no `asChild` in their API at all. Fixed by rewriting those
4 call sites to `render={...}`. Confirmed via `tsc --noEmit` before and
after. Worth remembering because it's an easy mistake to reintroduce:
most shadcn/ui examples online are Radix-based and use `asChild` —
**this codebase is Base UI. Always use `render`, never `asChild`.**

## Verification standard

Something counts as "verified" only once it's actually been run and the
output checked — not because the code looks correct or a document says
so. Treat every status claim, including the ones in this file, that way.
