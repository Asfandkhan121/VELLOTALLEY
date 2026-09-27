# HANDOFF v6: Real international bank profiles (not fabricated)

## Context

Previous session (`HANDOFF_v5.md`) flagged that HBL/UBL-international/Emirates
NBD/ADCB/Al Rajhi/NCB support was blocked on missing real sample PDFs, and
that Arabic/OCR support was a separate, unbuilt subsystem. This session, 17
real statement PDFs were uploaded (mostly for entities unrelated to the
Statement Converter's original scope — an IB brokerage account, Binance,
Bybit — but several were real UAE and one Swiss bank statement).

## What was actually verified this session (3 new profiles, real coordinates, real balances)

| Profile | Bank | Country | Real transactions parsed | Closing balance match |
|---|---|---|---|---|
| `wio` | Wio Bank | UAE | 4 | Exact (135,082.45 AED) |
| `adib` | Abu Dhabi Islamic Bank | UAE | 1 | Exact (20,695.34 AED) |
| `aaib` | AAIB (name not printed on statement itself) | UAE | 7 | Exact (247,739.35 AED) |

Total supported banks: **9** (mcb, samba, fwb, ubl, bop, allied, wio, adib,
aaib). All previously-verified profiles re-tested after these changes — no
regressions (26/6/347/317 transactions respectively, all still matching).

### Three real bugs found and fixed while building these (not hypothetical — each reproduced against the actual uploaded PDF)

1. **Wio**: the page header's "FROM 01/02/2025 TO 28/02/2025" line has its
   first date at x0=45; my initial (0,75) date-column bound caught it,
   creating two spurious "transactions" that swallowed the entire
   account-summary block as description text. Fixed by narrowing to (0,40) —
   real transaction dates sit at x0=23.
2. **ADIB**: credit column (500,545) also caught the adjacent Balance
   figure. `_amount()` returns the *last* number found in a column's text,
   so it silently returned the balance as the credit instead of the real
   0.00. Fixed by narrowing the credit column to end at 498.
3. **AAIB**: debits print with a leading "-" even though they're already in
   a dedicated Debit column (unlike every other 2-column profile, where
   position alone conveys debit/credit and magnitudes are unsigned). Without
   a fix, debit amounts were stored as negative numbers. Added an opt-in
   `unsign_debit_credit` profile flag (default off, so it can't silently
   mask a real sign issue in any other bank) and set it only for `aaib`.

### One data-quality finding worth flagging, not a code bug

AAIB's statement lists transactions **most-recent-first** (Dec 20 appears
before Dec 13). The existing forward balance-chain validation assumes
chronological order, so rows 2 onward get flagged `needs_review` even though
extraction is correct — the flags reflect a real mismatch between print
order and the validator's ascending-date assumption, not a parsing error.
Not fixed this session (would need either a resort-before-validate step or a
per-profile "reverse order" flag) — flagging for a future pass if AAIB
volume grows.

## What was investigated and explicitly NOT built, with concrete reasons

| File(s) | Why not |
|---|---|
| Interactive Brokers, Binance, Bybit, Maerki Baumann GBP "Portfolio statement" | Not transaction ledgers at all — NAV/PnL/position/performance reports. A different data model; adding a "profile" wouldn't make sense regardless of coordinates. |
| Maerki Baumann USD/AED/EUR/GBP "Position statement" (4 files, real transaction-ledger format, Switzerland) | **Zero extractable text** — confirmed via `pdfplumber`, all 4 files return 0 characters. These are image/vector-rendered PDFs, not real text-layer PDFs. Needs OCR, same blocker as the Arabic statements — not a coordinate problem. |
| Emirates NBD businessONLINE AED (WEEX, 41 real transactions — by far the richest dataset in the batch) | Architecturally doesn't fit the row-clustering model at all: within a single logical transaction, the transaction date + debit/credit sit on one physical line and the running balance sits on a *different* physical line (the multi-line wrapped narration pushes them apart). Confirmed by inspecting real word coordinates — this isn't guessable from bounds, it needs different parsing logic (e.g., matching balance to the nearest date-bearing row rather than the same row). Left unbuilt rather than force wrong coordinates onto real financial data. |
| DIB AED/EUR/USD (WEEX, bilingual Arabic/English) | Real finding: the actual transaction rows are plain Latin-script English (Arabic is a parallel header translation, not per-row bilingual data) — so this does NOT need OCR/RTL handling, undercutting part of the original ticket's assumption. But only 2 real transaction rows exist across all 3 statements combined (0 in EUR, 0 in USD) — too little to responsibly verify a profile against a real closing balance. |
| Emirates NBD EUR (WEEX) | Statement literally says "No Data" — zero transactions, nothing to build against. |
| Chinese bank (浙商银行/Zheshang, WEEX, CNY) | Only 5 real rows; not attempted this session for time, but has a real text layer and a clean single-line-per-transaction layout — a reasonable next candidate if prioritized. |

## IBAN detection re-validated against real data

`intl_parsing.detect_country_from_iban` / `extract_iban` (built last session
against zero real UAE IBANs, only synthetic fixtures) were run against 7 real
AE IBANs from this batch (Wio, Emirates NBD ×2, ADIB, DIB ×3) — all detected
correctly. The 2 Swiss (CH) IBANs correctly returned `None` (out of the
PK/AE/SA scope) rather than false-matching. No new bugs found here.

## Recommended next steps, in order of value

1. If Emirates NBD businessONLINE volume matters (it's the richest real
   dataset here), that's worth a dedicated pass to handle the
   split-across-physical-lines balance — not a quick fix, budget real time.
2. Chinese bank (Zheshang) is a quick win if wanted — real text layer, clean
   layout, just needs coordinates measured the same way as the others.
3. Maerki Baumann needs an OCR decision before anything else can happen with
   it, same as Arabic-only statements — bundle that decision together rather
   than solving it twice.
4. DIB needs more real sample statements with actual transaction volume
   before a profile can be responsibly verified — 2 rows isn't enough.
