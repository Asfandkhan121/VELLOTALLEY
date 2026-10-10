# ARCHITECTURE-ESSENTIALS.md — Vellotalley

Read this first. Full detail is in `ARCHITECTURE.md`.

## One-sentence version

FastAPI backend (`backend/`) + Supabase + Next.js frontend (`frontend/`,
shadcn/Base UI), nothing deployed yet, Phase 1 code-complete.

## Five things that will bite you if you forget them

1. **`needs_review = true` is unconditional** for anything the heuristic
   or LLM parser produces, and separately, the NLP layer's own
   ACCEPT/REVIEW decision must never be merged with it.
2. **Ownership checks are server-side**, against the real authenticated
   user ID. RLS is backup, not the only line of defense.
3. **Secrets never go in frontend code.** Service-role key and any
   configured LLM provider key — backend-only, always.
4. **`statement_notes`/`demand_signals` are read-and-store only.**
5. **Keep the product phases distinct.** Phase 1 is only bank-statement
   PDF-to-Excel conversion. Phase 2 categorizes raw cash books and other
   supporting records into reviewed Main Heads/Sub Heads. Phase 3 builds
   the Trial Balance and financial statements from reviewed data. Do not
   present future-phase workflows as implemented when they are not.

## The one frontend-specific trap

This codebase is **Base UI, not Radix**. Use `render={<Element/>}`, never
`asChild` — they look similar in shadcn/ui examples online but Base UI has
no `asChild` prop at all. This already caused a real, fixed bug once.

## Current blockers

1. No production deployment could be verified; the real login -> upload ->
   extract -> download flow has not been run against a reachable backend.
2. NLP Slice 1 is wired into extraction and transaction previews, but
   classifier, feedback, and learning tiers are not built.
3. Account deletion and the expanded privacy page are implemented in the
   repository, but deletion has only been tested with mocks. Production
   provider settings and live RLS policy drift still need review.

## Where things live

- Parser: `backend/statement_converter.py`, `backend/heuristic_parser.py`,
  `backend/llm_parser.py`.
- NLP layer: `backend/nlp/`.
- API: `backend/app/main.py`, `repository.py`, `config.py`.
- Migrations: `backend/database/`; compare repository files with deployed
  migration history before applying schema changes.
- Frontend: `frontend/app/`, `frontend/components/`, `frontend/lib/api.ts`
  (backend client), `frontend/proxy.ts` (the CORS-avoiding proxy).

## The one habit that matters most

"Verified" means actually run and checked, not "looks right" or "a
document said so." Say plainly when something is only reviewed, not run.
