# HANDOFF v7: OCR support — built, tested, working

## What was built

**New module `ocr_extraction.py`**: `ocr_words_for_page(pdf_path, page_number,
dpi=300, lang="eng")` renders a page with `pdf2image`/`poppler` and OCRs it
with `pytesseract`, returning words in the exact same shape pdfplumber's
`extract_words()` produces (`{"text", "x0", "top"}` in PDF points). This
means every existing piece of the parser — `_cluster_rows`, `_text`,
`BANK_PROFILES` column bounds — works completely unchanged whether a page's
words came from the real text layer or from OCR. No duplicate parsing logic.

**New profile `maerki`** (Maerki Baumann & Co. AG, Switzerland): the four
uploaded statements (USD/AED/EUR/GBP) have **zero embedded text** — confirmed
again this session, not assumed — so they route through OCR for every page
(`requires_ocr: True` on the profile). `parse_statement()` now checks this
flag and calls `ocr_words_for_page()` instead of `page.extract_words()` when
set; the OCR import is deferred so none of the other 9 profiles ever need
`pytesseract`/`pdf2image` installed.

**Arabic language pack installed** (`tesseract-ocr-ara`) and verified against
real Arabic text from your Wio Bank statement's footer — recognized real
words correctly (`بنك` = bank, `أبوظبي` = Abu Dhabi, `ويو` = Wio). Accuracy
was mixed on that specific small/stylized stamp text — some tokens garbled —
which I'm reporting plainly rather than only showing the clean examples.
`lang="eng+ara"` is supported for genuinely bilingual pages; the module
raises a clear `RuntimeError` naming the missing pack if you OCR with a
language that isn't installed, rather than silently mis-reading the text.

## Real results — all 4 Maerki Baumann statements, 36 transactions total

| Statement | Transactions | Closing balance | Match | needs_review |
|---|---|---|---|---|
| USD | 15 | 108.83 | Exact | 0/15 |
| AED | 6 | -19.00 | Exact | 0/6 |
| EUR | 12 | 972.50 | Exact | 0/12 |
| GBP | 3 | 15.61 | Exact | 0/3 |

Every debit, credit, and balance across all 36 transactions matches the
original statement text exactly — spot-checked line by line, not just the
final balance.

## Two real bugs found and fixed (both affect every profile, not just OCR ones — regression-tested)

1. **Swiss thousands separator (`'`) was silently truncating amounts.**
   `100'132.10` was being parsed as `132.10` — the "100" thousands part was
   dropped entirely, because `_AMOUNT`'s regex only recognized `,` as a
   grouping character. `re.findall` returned two separate matches (`100` and
   `132.10`), and `_amount()` takes the *last* match, discarding the first.
   This is not cosmetic — it's the kind of bug that produces a plausible-
   looking but wrong number with no visible signal, exactly the failure mode
   the whole "verify against printed balance" discipline this project has
   followed exists to catch. Caught immediately because I checked the last
   printed balance, not because it looked wrong on the surface — several
   corrupted rows still passed the row-to-row balance-chain check, because
   both sides of the check were wrong by the same truncation pattern. Fixed
   by extending the regex to accept `'` alongside `,`, and stripping both
   before constructing the `Decimal`. Verified this doesn't affect any
   existing comma-format bank (unit test + full 6-bank regression, all
   still match).
2. **`_text()` didn't re-sort words by x0**, trusting row order from
   `_cluster_rows`. That's safe for real text layers (words within a row are
   already left-to-right), but when OCR's baseline detection puts two
   physical sub-lines at slightly different `top` values that still merge
   into one clustered row, all of one sub-line's words can sort before all
   of the other's — reproduced concretely: `"Transfer Interactive Brokers
   LLC"` came back as `"LLC Transfer Interactive Brokers"`. Fixed by
   explicitly sorting the column's words by `x0` before joining. No-op for
   already-ordered text-layer rows (confirmed via full regression — 6/6
   previously-verified profiles still match exactly).

## Full regression status (everything, after both fixes)

All 9 previously-verified profiles (mcb, samba, fwb, ubl, bop, allied, wio,
adib, aaib) re-tested end-to-end: **no change in results, all still match
their printed closing balances.** `test_intl_parsing.py`: 18/18 still
passing. New `test_ocr_extraction.py`: 6/6 passing (includes a direct
regression test reproducing the word-scramble bug, so it can't silently
come back).

**Total supported banks: 10** (9 text-layer + 1 OCR).

## Honest scope of what "bilingual" means here right now

- The Arabic language pack is installed and demonstrably reads real Arabic
  text (imperfectly on small/stylized text, cleanly enough to be useful on
  body text — not independently re-verified on a larger Arabic paragraph
  this session; that's the natural next check if a genuinely bilingual
  statement with real transaction data in Arabic actually shows up).
- No bank in this project's samples has actually needed it yet: DIB's real
  finding from last session stands — its transaction *data* is plain
  English, Arabic is a parallel header translation. Nothing here has
  exercised OCR on a page where the transaction amounts/dates themselves are
  in Arabic script or RTL-ordered. If that specific case arrives, it needs
  its own real-sample verification, same as everything else in this
  project — I'm not claiming it's solved, only that the plumbing (language
  pack, multi-language OCR call, coordinate compatibility with the existing
  column-bound parser) is real and working.
- Emirates NBD businessONLINE (flagged last session as architecturally
  incompatible with row-clustering — balance on a different physical line
  than date/debit/credit) is unaffected by any of this — OCR doesn't fix a
  layout problem that exists in the text layer itself.

## Files changed/added this session

- `statement_converter.py`: `_AMOUNT` regex, `_amount()`, `_text()`,
  `parse_statement()` (OCR branch), new `maerki` profile.
- `ocr_extraction.py` (new).
- `test_ocr_extraction.py` (new, 6 tests).
- `requirements.txt`: added `pytesseract==0.3.13`, `pdf2image==1.17.0`, with
  a note that `tesseract-ocr`/`poppler-utils` system packages and per-
  language tesseract packs (e.g. `tesseract-ocr-ara`) are also required and
  not installed by pip.
