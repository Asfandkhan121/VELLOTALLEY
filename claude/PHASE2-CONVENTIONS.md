# Phase 2 Conventions and Handoff (updated 2026-10-07, sixth pass)

Status: **analysis and rulings complete for this pass; first code slice (canonical head tables) pushed as three stacked PRs (#8, #9, #10), open, NOT merged. Migration SQL (identical to PR #8's 0008 file, no seed) WAS applied to the live Supabase project on 2026-10-07 under the name `add_account_heads`; the live tables are empty.** Rule 8 was lifted by the owner for this groundwork because categorized cash books now supply real classification data; the owner then explicitly chose "head tables" as the first code slice. Phase 3 and Stripe remain gated as before. See section 7 for the slice status. A second slice (dimension discovery, PR #11) is described in `claude/HANDOFF-dimension-discovery.md`.

## 1. Owner rulings (stated by the owner)
1. All SSES/POF units are on **accrual basis**. Accounting basis is a per-organization setting; if unset, payroll/income rows get `needs_review` and nothing is guessed.
2. **Payroll (EOBI/CPF/PESSI and related benefits)**
   - Cash-book payment: clears the liability, for the amount actually paid (accrual). On cash basis the payment itself is the expense.
   - Expense: employer share only (confirmed), calculated from the salary workings for the year. Always manual input / uploaded source, never inferred from the cash book.
3. **Income**: same logic. On accrual, the cash receipt clears the receivable (Dr Bank, Cr Fees & Funds Receivable) and income is recognized by a separate accrual journal for the amount earned. On cash basis the receipt is the income.
4. The cleaned GLs are double-entry, built by the owner from raw multi-sheet cash books, bank statements and a salary working file.
5. The head tables must also be reflected in the frontend (owner request, 2026-10-07).
6. The code must read the available data and create columns only for what is present (e.g. a branch column only if narrations show recurring branches); the recurring word differs per client (owner request, 2026-10-09).

## 2. Data received (all SSES/POF school units)
Raw-to-GL pairs: C1 (RAR: Samba/BOP/Islami tabs) -> C1_Gl.xlsx; Campus 7 (zip of 12 .xls) -> c71.xlsx; C-IX (Cash_Book_25-2026Updated) -> c9.xlsx; C-II (Askari + Samba) -> c2.xlsx; centralized (Cash_Book_Islamic, Revised_Cash_Book, Cheque_Record) -> centralized GL. Also: 10 bank-statement PDFs + 1 HTML-disguised-as-.xls (BOP PLS+CDA, Askari, MCB 8828/1251/1740, UBL savings, two SMP/"ENT BOOK" statements, one 19-page "MB.STMT" statement, one .xls) and the 13-sheet salary working (CONSOLIDATED_GL). Later (2026-10-09): CB_25.xlsx, a single-sheet FY2024-25 cash book (611 rows, mostly ABL) with its own 17-main-head taxonomy; unit unknown, no matching GL.

## 3. Findings
Verified = a script was run and its output checked. Reviewed = looked at, not run. Matching everywhere is exact date+amount (a floor) unless stated.

**Cross-unit**
- **[verified] Taxonomy drifts across files.** ~223 distinct sub heads, ~254 raw head/sub-head pairs; synonyms ("Liabilities" vs "Accrued and Other Liabilities", "WHT Payable" vs "Withholding Tax Payable"), typos. A draft variant->canonical map exists; it is **a proposal, not confirmed by the owner**.
- **[verified] CB_25 uses another taxonomy:** 17 main heads / 83 pairs (e.g. "Receivable from campuses against Security Guard", "Intra society receivable"); only 23% of its rows use a sub head already in the proposed seed; the campus number is baked into the sub head; variants such as "Income"/"Income " and "Receivable from against X"/"Receivable from campuses against X"; 18 same-day repeated rows; its bottom totals do not tie to its transaction table (observation only).
- **[verified] Year bug.** Aug-Dec journal rows carry 2026 instead of 2025 in all 13 sheets of the salary workbook and all 5 GLs (82-109 future-dated rows each). Corrected copies (Aug-Dec 2026 -> 2025) delivered with a changelog; 7 July-2026 rows left for owner decision. **Not opened in Excel**; compared cell-by-cell in code. The rule also changed ~5 non-payroll dates in c9. The generator still needs fixing.
- All sources are one sector (schools); nothing validates the taxonomy for other sectors.

**Per-unit alignment (raw cash book vs GL non-bank rows)**
| Unit | Raw lines | Matched date+amount | Narration -> sub head | Quality as a training pair |
|---|---|---|---|---|
| C9 | 762 | 760 of 762 raw (2 unmatched: W/H Tax, one dated 2024) | All 653 repeated-narration rows predicted right (leave-one-out), but 567 are one narration; excluding it 86/86; 106 of 192 other rows are unique narrations | **Good**. 14% of rows need fuzzy/semantic matching or review |
| centralized | 560 | 551 of 768 GL rows (71%); 9 raw unmatched | 96% same-sub-head on repeated narrations, 2 narrations ambiguous | **Good**, but GL notes say heavy free-text, combined narrations, 47 "Requires Clarification" rows; raw covers Dec-25 to Jun-26 only |
| C7 | 326 | 255 of 764 GL rows (33%) | ~235 rows in ambiguous narrations, mostly payroll/reclass journals | **Partial**: rest of the GL is payroll (~180) and fee-receivable journals (~130), ~190 untraced; raw nearly empty from Feb 2026 |
| C1 | 439 scraped | 248 of 878 GL rows (28%); 42% by amount only | 73% same-sub-head on repeated narrations, 111 ambiguous | **Weak**: GL has 7 bank accounts, raw covers some; scraper is generic and stale tabs mix months |
| C2 | 257 | 148 of 257 raw by amount only (no dates on receipts) | 8 of 113 raw descriptions map to >1 class, some false pairings | **Weak**: raw is a bank reconciliation statement with lump-sum receipts, undated, unpresented cheques repeated across months |

C1 and C2 numbers are indicative only: the scraper is generic, stale/duplicate tabs were not filtered, and amount-only matches produce false pairs. Do not use them for design decisions.

**Other**
- **[reviewed] Raw data quality:** C-II Askari Feb/Mar/Apr 2026 opening balances identical (2,160,959.15); Apr sheet header says "1st Jan 26"; Samba has no May 26 sheet; RAR Dec-25/Jun-26 files have tabs titled for other months and a mislabeled file name; C9 has a W/H Tax line dated 2024.
- **[verified, C7] Bank statements (BOP PLS/CDA, 353 lines)** add only 6 matches to unmatched GL rows. The remaining unexplained C7 rows are not from the BOP statement.
- **[verified, identification only] Statement inventory:** BOP PLS 348 dated lines, BOP CDA 8, Askari 186, MCB 1251 65, MCB 8828 51, MCB 1740 18, UBL savings 29; two SMP statements and the 19-page MB.STMT use a date format my identifier didn't count (not parsed). Nothing beyond BOP/C7 aligned to a GL.

## 4. Design implications for Phase 2
- Split into **cash-side rows** (payments/receipts: auto-proposed from narration + payment type, `needs_review=true` always, per rule 2) and **accrual-side rows** (payroll expense, income accrual, receivable reclass: generated only from an uploaded source such as salary workings or fee data, or entered manually; never inferred from the cash book).
- Basis setting per org, default unset.
- Normalize variants to canonical heads before learning; the canonical list needs owner sign-off.
- Columns such as branch are discovered from the data (PR #11), never assumed.
- Best training data first: C9 and centralized (high coverage, consistent narration -> class). Expect ~14% of rows (unique narrations) to need fuzzy/semantic matching or review; the self-hosted NLP layer's ACCEPT/REVIEW stays separate from `needs_review` and `statements.confidence` (rules 2, 7). `statement_notes` / `demand_signals` stay read-and-store only (rule 6).

## 5. Open items
1. Owner review of the normalization map and the proposed head seed (**114 heads, 135 aliases**, after the fix below). A review sheet (`seed_review.csv`, 114 rows, 85 flagged as near-duplicate/variant groups) was delivered; near-duplicates such as CPF / CPF Payable / CPF Contribution need decisions. The seed is NOT loaded in the live database.
2. The 7 July-2026 rows left unchanged; fix the salary-file generator's year bug.
3. Untraced ~190 C7 rows and C7's Feb-Jun 2026 raw gap.
4. Proper per-tab raw parsing for C1 and C2 before trusting their numbers.
5. Parse the remaining bank statements and align to the GLs.
6. Default basis for a new, non-SSES user.
7. Owner review and merge of PRs #8, #9, #10 in order (and #11, independent). The live DB already has the tables, so merging only brings `main` in line with it; do NOT re-run the migration live.
8. **Migration numbering drift:** the live migration history has two `0008_*` entries (`0008_drop_duplicate_confidence_constraint`, `0008_performance_and_security_hardening`) that are not in the repo's `backend/database/`, and the repo's new `0008_add_account_heads.sql` shares that number; live name for it is `add_account_heads`. Owner to decide whether to renumber the file and whether to back-fill the two untracked live migrations into the repo.
9. No code reads the head tables for classification yet; the next code slice (cash-side rules) needs explicit owner go-ahead.
10. Revoke the GitHub token the owner pasted in chat on 2026-10-07 (not needed in the end, never written to a file, git config or memory, but it is in the chat transcript).
11. Pre-existing Supabase security advisor warning (unrelated to this slice): Auth "Leaked Password Protection Disabled".

## 6. Self-contained prompt for the next session
"Project: Vellotalley (see project instructions; repo Asfandkhan121/VELLOTALLEY). Read claude/PHASE2-CONVENTIONS.md and claude/HANDOFF-dimension-discovery.md first. Rule 8 was lifted by the owner for Phase 2 groundwork. The first code slice (canonical head tables) is in three stacked PRs: #8 (`claude/account-heads`, base main), #9 (`claude/account-heads-api`, base #8's branch), #10 (`claude/account-heads-ui`, base #9's branch); PR #11 (`claude/dimension-discovery`) is independent. Check their current state and mergeable_state via the REST API first, and clone fresh. The migration SQL is ALREADY applied to the live Supabase project (xujijonwxxoxxtvhorfi, migration name `add_account_heads`, empty tables, no seed): never re-run it; verify with list_tables/list_migrations. Do not load the proposed seed or apply any other migration without explicit approval. The owner's accrual/cash rulings are in section 1. Next steps, one at a time and only with the owner's go-ahead: owner review/merge of the PRs and the seed, then (separately) cash-side rules. Pushing: in this environment the git proxy only allows repos attached with the add_repo tool (access: push); the owner's token may not be needed. If a token is used it must be inline only and revoked afterward. Hold needs_review=true unconditional; keep the NLP ACCEPT/REVIEW decision separate from it."

## 7. Slice 1 status: canonical head tables
Three stacked branches off main (067a62c), each its own piece per rule 1. **Pushed 2026-10-07; PRs open, not merged.**
| PR | Branch (base) | Tip commit | Contents |
|---|---|---|---|
| #8 | `claude/account-heads` (main) | 5b53d9a | `backend/database/0008_add_account_heads.sql` (tables `account_heads`, `account_head_aliases`; main head limited to 6; RLS: authenticated read, no write policies); `backend/database/proposed/account_heads_seed.sql` (**114 heads, 135 aliases**, script-derived, **not owner-approved, deliberately outside the numbered migrations**); `backend/test_account_heads_seed.py` (3 static tests) |
| #9 | `claude/account-heads-api` (`claude/account-heads`) | 43b42ba (merge of #8 tip) | `GET /v1/account-heads` (bearer auth required, read-only, global reference data), `SupabaseRepository.list_account_heads`, `backend/test_account_heads_api.py` (3 tests) |
| #10 | `claude/account-heads-ui` (`claude/account-heads-api`) | 11c805b (merge of #9 tip) | read-only "Chart of accounts" page (`/chart-of-accounts`), nav item, SWR hook/type, auth-gated route prefix in `lib/supabase/proxy.ts` |

All three reported `mergeable_state=clean` via the REST API on 2026-10-10.

**Seed bug found and fixed by me (commit 5b53d9a, "Fix proposed seed: drop bogus "(bank-side)" head, keep acronym casing"):** the first seed generator turned a placeholder sub head "(bank-side)" into a head and an alias, contradicting the seed's own note that bank-side rows are not heads. Fix: generator skips placeholder subs starting with "(", and uppercases acronyms (CPF, EOBI, PESSI, WHT, SSES, IBFT, HO, PLS, PTCL, IDP). The static test now also asserts no head/alias target starts with "(" (verified: it fails on the old seed, passes on the new one). Seed went from 115/136 to 114/135. Live DB unaffected (no seed loaded).

**Live database (done 2026-10-07, owner chose "apply migration live", then delegated the timing to my judgment; applied before PR #8 was merged):**
- Pre-check: no `account_heads` / `account_head_aliases` tables existed; live tables were clients, statements, transactions, statement_notes, demand_signals.
- Applied via the Supabase `apply_migration` tool with SQL identical to the PR #8 file (comments stripped), name `add_account_heads`. Result: success.
- **Verified live (queried):** both tables exist with RLS enabled and exactly one policy each (SELECT for `authenticated`; no write policies). Security advisor shows no new warnings; its only finding is the pre-existing Auth "Leaked Password Protection Disabled".
- Tables are empty (no seed loaded), so the page shows "No account heads yet". The endpoint and page against the live DB have not been exercised.

**Verified (run, with evidence):**
- Migration + seed applied to a real local Postgres 16: bad main head, duplicate head, un-normalized alias and duplicate alias all rejected; with Supabase-style grants an `authenticated` role reads all heads, cannot insert (RLS error) and a delete affects 0 rows. Re-run on the fixed seed: 114 heads / 135 aliases, 0 placeholder heads.
- **From a fresh GitHub clone of the pushed tip (rule 9):** `claude/account-heads-ui` at 11c805b contains the account-heads files, the seed has 0 occurrences of "bank-side", and the backend suite gives 85 passed. Checking out 5b53d9a (PR #8 tip): 82 passed. Earlier tips (faff56f, 424fcfa, 89423a4) were also verified from fresh clones; frontend at 89423a4 had `tsc --noEmit` clean and `next build` listing `/chart-of-accounts`. **The frontend was not re-built at 11c805b** (the merge only brought in the seed/test change, no frontend files changed).
- **The frontend build needed a temporary font stub because this sandbox cannot reach Google Fonts**; the stub was reverted (`git diff app/layout.tsx` clean). The real build with Google Fonts was not run here.
- Diff checked for `asChild` (rule 5) and for secrets (rule 4): none found.

**Reported only / not verified:**
- The frontend page and the endpoint were not exercised against the live DB or in a browser; no frontend tests exist for the page.
- No CI result checked.
- Frontend has no per-user data on this page, so there is no ownership filter; the backend endpoint still requires a valid token (rule 3 is not engaged for global reference data).

**Note on pushing:** the first push attempt with the owner's token in the URL was refused by the session's git proxy ("repository not in this session's authorized set"). Attaching the repo via the add_repo tool (push access) fixed it, after which pushes went through the proxy without the pasted token.
