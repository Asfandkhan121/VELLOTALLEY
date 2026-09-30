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
3. **Secrets never go in frontend code.** Service-role key, Anthropic key
   — backend-only, always.
4. **`statement_notes`/`demand_signals` are read-and-store only.**
5. **Don't build Phase 2/3** (categorization, Trial Balance, financial
   statements) until Phase 1 has real usage data.

## The one frontend-specific trap

This codebase is **Base UI, not Radix**. Use `render={<Element/>}`, never
`asChild` — they look similar in shadcn/ui examples online but Base UI has
no `asChild` prop at all. This already caused a real, fixed bug once.

## Current blockers

1. Nothing deployed anywhere.
2. Real end-to-end flow (real login -> upload -> extract -> download) has
   never happened against a reachable backend.
3. NLP Slice 1 not yet wired into the extraction endpoint.

## Where things live

- Parser: `backend/statement_converter.py`, `backend/heuristic_parser.py`,
  `backend/llm_parser.py`.
- NLP layer: `backend/nlp/`.
- API: `backend/app/main.py`, `repository.py`, `config.py`.
- Migrations: `backend/database/0001` through `0008`.
- Frontend: `frontend/app/`, `frontend/components/`, `frontend/lib/api.ts`
  (backend client), `frontend/proxy.ts` (the CORS-avoiding proxy).

## The one habit that matters most

"Verified" means actually run and checked, not "looks right" or "a
document said so." Say plainly when something is only reviewed, not run.
