# CLAUDE.md

This project follows `AGENTS.md` — read that first. This file only adds
what's specific to working here *as Claude*.

## Persistent context across sessions

Prior context lives under `/areas/pk-bank-statement-converter.md` in
memory (aliases include Vellotalley, Ledgerly, bank statement converter).
Read it before assuming a fresh start.

## Tools available

- **Supabase MCP connector** — direct access to the live project (ref
  `xujijonwxxoxxtvhorfi`). Query the actual schema/advisors rather than
  trusting a document's description of database state.
- **A sandboxed container** for git, pip/npm/pnpm, type-checking, and
  building. Registry access has been inconsistent across sessions — check
  before assuming something can't be verified.
- **`create_file` for every deliverable.**

## GitHub, concretely

This repo (`Asfandkhan121/VELLOTALLEY`) is the source of truth. Clone it
fresh each session. No standing push credential exists — the human
supplies a short-lived, single-repo fine-grained token per session when
a push is needed. Use it only inline in shell commands, confirm afterward
that it isn't sitting in `.git/config`, and remind the human to revoke it.
Push to a `claude/<topic>` branch and open a PR; never push to `main`.
Verify the pushed branch by cloning it fresh from GitHub (not the local
working copy) and running the real tests/build against that clean clone.

## The handoff-file habit, concretely

At the end of any step that changes state, write a handoff file (numbered,
superseding the previous one): what changed, what was independently
verified vs. only reported, what's still open, and a self-contained
"prompt for the next AI." This has been the single most consistent
request in this project's history.

## A pattern worth knowing about

More than once, a "done" claim in an uploaded document turned out to be
stale or contradicted once directly checked against the real database,
codebase, or build output. Read status claims — including this file's —
as things to verify, not as ground truth.
