# Handoff: per-client accounting basis (migration only) (2026-10-10)

Read claude/PHASE2-CONVENTIONS.md first. Its status lines are stale: slices #8-#14 are merged on main `8c03941065`. Live Supabase (`xujijonwxxoxxtvhorfi`) has `account_heads`, `account_head_aliases`, and `client_account_heads`, all empty (owner, 2026-10-10). Do not re-run `0008` or `0009`. The proposed seed is not loaded.

`claude/HANDOFF-client-heads-ui.md` is not in the repo. PR #16 is the UI slice; this file is the handoff for the basis column only.

## PR state checked via REST (authenticated, 2026-10-10)
- #15 `claude/client-heads-endpoints` `591f5a35` -> `main` `8c03941065`: open, mergeable_state=clean. Propose / confirm / list client heads. Stores nothing until confirm. Does not set a basis.
- #16 `claude/client-heads-ui` `50d83dd` -> #15: open, mergeable_state=clean. Page `/clients/{id}/heads`. Shows `stated_basis` and accrual evidence as text only. Confirm saves heads, not a basis. No frontend build was claimed beyond `tsc --noEmit`.

## What this slice changes
- `backend/database/0010_add_client_accounting_basis.sql`: adds `clients.accounting_basis text not null default 'unset'` with check `accrual | cash | modified_cash | unset`.
- `backend/test_client_accounting_basis_migration.py`: static checks only.
- No API, no questions UI, no live apply. Existing clients become `unset` via the default, not accrual. SSES/POF stay an owner ruling, not a row update.

Unset still means payroll and income rows get `needs_review` and nothing is guessed. That behavior is not implemented in this file. Heuristic and LLM extraction rows stay `needs_review=true` unconditionally. This migration does not read or write `needs_review` or `statements.confidence`.

## Verified
- Static tests run here: `pytest backend/test_client_accounting_basis_migration.py backend/test_client_account_heads_migration.py backend/test_account_heads_seed.py` -> 10 passed.
- After push, re-clone the branch and re-run that command. Record the result in the PR if it differs.

## Not verified
- Not applied to Postgres (no local server) and not applied to the live Supabase project.
- Basis questions, a recommend-and-confirm endpoint, and the `needs_review` behavior for unset payroll/income are not built.

## Still open
Do not apply `0010` live without an explicit go-ahead. Next slice, only with go-ahead: questions that recommend a basis and an authenticated endpoint that stores the user's confirmation on this column. Do not infer the basis from the trial-balance reader. Do not start cash-side classification, Phase 3, or Stripe.

## Next-session prompt
"Project: Vellotalley. Read claude/PHASE2-CONVENTIONS.md and claude/HANDOFF-accounting-basis.md. Clone fresh. PR for `0010_add_client_accounting_basis.sql` adds clients.accounting_basis (accrual/cash/modified_cash/unset, default unset) and is NOT applied live. Check that PR via REST before doing anything else. Do not apply the migration without an explicit go-ahead. Next only with go-ahead: basis questions plus an authenticated confirm endpoint that writes this column from the signed-in user. A recommendation is not a saved basis. Unset keeps payroll/income on needs_review. needs_review=true stays unconditional for heuristic/LLM rows."
