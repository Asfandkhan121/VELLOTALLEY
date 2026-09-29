# ROADMAP: Statement Converter → Bank/Cash Books → General Ledger + Chat

## The three phases, as I understand them now

1. **Phase 1 (free): Statement Converter.** PDF bank statement → clean
   Excel. This is what's been built so far — 10 real bank profiles, OCR
   fallback, FastAPI backend, Supabase persistence.
2. **Phase 2 (paid?): Bank books / cash books.** Takes Phase 1's output and
   turns it into something more directly usable for bookkeeping — this
   matches the cash-book consolidation work already done for other clients
   (Sir Syed High School, POF Model Primary School Campus-7) in earlier,
   separate sessions: Main Head/Sub Head classification, multi-account
   consolidation, pivot-ready single-sheet format.
3. **Phase 3 (premium): General ledgers + the "chat box".** Full
   double-entry ledger generation, and the personalized/demand-driven
   assistant described in the last message — profile-aware, follows
   real usage trends, eventually proposes (not silently applies) parsing
   and classification improvements for a human to approve.

## Your question: should I prepare for all 3 phases starting now?

Short answer: **prepare the foundation, don't build the features.** Those
are different things, and conflating them is the actual risk — not moving
too slowly, but locking in phase-2/3 assumptions before phase 1 has taught
you anything real about how people actually use it.

### Why not build ahead

You don't yet know, from real usage, which banks people actually need,
which cash-book/classification conventions actually recur across clients,
or what "premium chat" commands people would actually type. Guessing that
now means building the wrong thing confidently. This is also the literal
reason the demand-signal logging just built matters: it's the mechanism
that turns "guessing what Phase 2/3 should look like" into "reading what
real usage actually says" — but only after Phase 1 has been out and used.
Building Phase 2/3 machinery before that data exists defeats the purpose
of collecting it.

This isn't a new opinion I'm introducing — it's the exact rule that's been
in every handoff since the start of this project: *"Build one milestone at
a time... Do not start [the next phase] until [this phase] is fully tested
and approved by a human."* I'm reaffirming it here because the reasoning
matters more than the rule: it's not caution for its own sake, it's that
premature architecture is a real cost (wrong data model, wrong assumptions
baked into schema/API shape) that's expensive to unwind later, whereas a
clean, extensible Phase 1 costs nothing to extend once you actually know
what Phase 2 needs.

### What IS worth doing now (cheap, low-risk, done or startable today)

- **Demand-signal logging** (`0005_add_demand_signals.sql`, live as of this
  session): every time someone requests a bank we don't support, that's
  now a row in a table instead of a discarded 422. This is the actual
  "system follows the trend" mechanism, in its safe form — real data,
  decided by a human reading it, not autonomous behavior.
- **Notes/feedback storage** (`0004_add_statement_notes.sql`, also live):
  the same idea applied to corrections and quirks, per statement.
- **The existing schema already has your "profile" seed.** Every `client`,
  `statement`, and now `note`/`demand_signal` is tied to `auth.users(id)`.
  A future `user_profiles` table (subscription tier, plan, usage counters)
  is a cheap additive migration *when Phase 2/3 billing actually starts* —
  there's no reason to build it before then, and no cost to waiting, since
  it doesn't require restructuring anything that exists today.
- **Keep an eye on what recurs across sessions.** The cash-book
  consolidation pattern (Main Head/Sub Head columns, multi-account
  merging) has already shown up multiple times for different clients in
  separate work outside this converter project. That's itself a real,
  already-observed demand signal for Phase 2 — worth remembering, not
  worth building yet.

### What should explicitly wait for Phase 1 approval

- Any Stripe/billing/subscription-tier code.
- Cash-book/general-ledger generation logic itself.
- The LLM "chat" layer (model choice, propose-and-approve UI, how
  suggestions get scoped per-client vs. shared bank profile) — flagged
  last session as needing an explicit decision, still true, and doubly true
  now that Phase 3 is explicitly premium: the cost/complexity of an LLM
  integration should be justified by paying users' actual demand for it,
  which Phase 1 usage data plus notes/demand-signals will show you.

## Practical next step

Ship Phase 1, let real people use it, let `demand_signals` and
`statement_notes` accumulate for a while. When you're ready to start Phase
2, the honest move is to come back with: which banks got requested most,
which note patterns recur, and what the cash-book work from other clients
has already taught about what a "more usable" output actually needs to
look like. That turns Phase 2's design into something grounded in real
data instead of a guess — which is the whole point of what you described.
