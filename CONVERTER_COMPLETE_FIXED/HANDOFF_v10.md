# HANDOFF v10: Notes/feedback storage — the real, safe first slice

## What was asked

"Make the code more accurate with every use", add a "chat option" for
personalized commands, and have the code "store information to make itself
more accurate by time and use."

## Why this wasn't built as one big autonomous system

Those three asks, taken literally and combined, describe a system where free-
text user input automatically rewrites how a financial parser reads debit/
credit/balance columns. For a tool whose entire value proposition is "the
numbers are exactly right" — the standard this whole project has been held
to, verifying every profile against a real printed closing balance before
trusting it — that's a real correctness risk, not a nice-to-have shortcut.
An ambiguous or malformed instruction silently changing parsing behavior
could corrupt a client's financial statement with no visible signal. I'm not
going to build that without an explicit, informed decision that this is
actually wanted, given what's at stake.

## What was built instead: a real, working, human-in-the-loop notes system

This is the honest version of "the code stores information to make itself
more accurate over time" for a deterministic, coordinate-based parser: a
place to accumulate structured feedback that a human (or a future,
explicitly-scoped review step) reads and acts on — not a black box that
edits its own logic.

**Migration `0004_add_statement_notes.sql`** (applied live, verified):
`statement_notes` table — `statement_id`, `user_id`, free-text `note`
(1-2000 chars), `created_at`. RLS policy matches the existing owner-scoped
pattern exactly (`auth.uid() = user_id`, same shape as `clients_owner_all`/
`statements_owner_all`/`transactions_owner_all`).

**Two new endpoints**, same ownership/validation discipline as every
existing endpoint:
- `POST /v1/statements/{id}/notes` — attach a note. 422 on empty or >2000
  chars, 404 if the statement isn't yours.
- `GET /v1/statements/{id}/notes` — list your notes on a statement, newest
  first.

**Tested the same way as everything else in this project**: 24/24 checks
pass via the `TestClient` + fake-repository harness (18 pre-existing +
6 new), migration applied and RLS policy confirmed live against the real
Supabase project, full regression re-run against 3 real bank PDFs (UBL, BOP,
Maerki Baumann) — all still match their printed closing balances exactly.

## What this unlocks right now (usable today, no further work needed)

A bookkeeper can leave themselves or a colleague a note on a statement:
"this account's dates are DD/MM not MM/DD", "ignore rows containing 'bank
fee'", "client confirmed the June opening balance is correct despite the
flag." That's real, immediately useful, and it's the actual mechanism by
which a human refines a bank profile over time — they read accumulated
notes across many statements from the same bank and update
`BANK_PROFILES` accordingly, the same way every profile in this project
has been built and fixed so far.

## What it deliberately does NOT do yet — needs an explicit decision

1. **Notes don't auto-apply to parsing.** No code currently reads a note
   and changes column bounds, date formats, or debit/credit logic. That's
   the boundary described above.
2. **No chat/LLM interface yet.** "Personalized commands" as literally
   described implies natural-language input, which implies an LLM in the
   loop somewhere. That's a real architecture and cost decision (which
   model, what it's allowed to do, how its output gets reviewed before
   taking effect) that shouldn't be guessed at silently.

## A concrete, safe path to what you actually described, if you want it

The natural next step that gets you real "personalized commands" without
the correctness risk: an LLM reads a statement's notes plus its extracted
transactions and **proposes** a specific, human-readable change (e.g. "swap
the date format to DD/MM for this bank profile") — a human clicks approve,
and only then does the change take effect. The LLM suggests; it never
silently rewrites. That's buildable as a real next milestone if you confirm
it's what you want — it needs a decision on which LLM/API to call and how
proposed changes get surfaced for approval, which I'd rather confirm with
you than assume.

## Question for you

Is the notes system enough for now, or do you want me to start on the
propose-and-approve LLM layer on top of it? And if the latter — do you want
suggestions applied per-client, or genuinely learned into the shared bank
profile (affecting every client using that bank)? Those are different
scopes and I want to build the one you actually need.
