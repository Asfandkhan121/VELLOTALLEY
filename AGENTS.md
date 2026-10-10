# AGENTS.md

Instructions for any AI agent working in this repository. Read
`ARCHITECTURE-ESSENTIALS.md` and `PRODUCT.md` first; this file is the
behavioral contract.

## Non-negotiable rules

1. **Build incrementally, one piece at a time.** Never scaffold an entire
   app, feature, or milestone in one shot.
2. **`needs_review = true` is unconditional** for every row the heuristic
   or LLM fallback parser produces. The NLP layer's separate ACCEPT/
   REVIEW decision must never be merged with this field or with
   `statements.confidence`.
3. **Preserve existing working code.** Change the parser, exporter, or
   backend only for a specific, reproduced bug.
4. **Ownership checks are server-side, always.**
5. **Secrets stay server-side** — the Supabase service-role key and the
   Anthropic API key never appear in frontend code, and never in this
   repo's git history going forward. Check explicitly whenever touching
   frontend code.
6. **`statement_notes`/`demand_signals` are read-and-store only.**
7. **Phase 2 and Phase 3 are authorized for incremental implementation**
   as defined in `PRODUCT.md`: Phase 2 categorizes raw cash books and
   supporting data into reviewed Main Heads/Sub Heads; Phase 3 prepares a
   Trial Balance and reviewed financial statements from that data. The
   owner authorized this roadmap on 2026-10-10. Preserve accounting
   safeguards and do not claim a phase is complete until its end-to-end
   workflow is implemented and verified.
8. **Do not start Stripe/billing** until the frontend is fully built,
   deployed, and working end-to-end.
9. **This frontend is Base UI, not Radix** — use `render={<Element/>}`,
   never `asChild`. This has already caused one real bug.
10. **Hold every claim to one standard: verified means actually run and
    checked, with evidence.** Say so plainly when you haven't.
11. **At every step, produce a handoff**: what's done (verified vs.
    reported-only clearly separated), what remains, and a reusable prompt
    for the next agent.

## GitHub workflow

- Clone fresh at the start of a session; don't assume a stale local copy
  matches `main`.
- Commit only to `claude/<topic>` branches, open a PR, let the human
  merge. Never push to `main` directly.
- Pushing needs a short-lived, single-repo, Contents + Pull-requests
  read/write token supplied by the human for that session. Use it inline
  in commands only — never write it to a file, git config, or memory.
  Remind the human to revoke it afterward.
- Verify every pushed branch by cloning it fresh from GitHub and running
  the real tests/build there, not just locally.

## Before a destructive or irreversible change

Ask first for anything on the live database (deleting rows/users,
rotating keys) that can't be undone by re-running a script. A PR the
human reviews before merging is not "destructive" in this sense — restructuring
files inside a PR is fine; force-pushing over history or deleting the
human's branches is not.

## Where to look

- `PRODUCT.md` — vision, tiers, phase roadmap.
- `ARCHITECTURE.md` — full technical detail.
- `ARCHITECTURE-ESSENTIALS.md` — five-minute version.
- `CLAUDE.md` — Claude-specific notes, if any diverge from this file.
