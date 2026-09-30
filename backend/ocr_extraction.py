"""OCR fallback word extraction for PDFs with no embedded text layer.

Used when pdfplumber's extract_words() returns nothing for a page -- i.e.
the PDF is scanned/rendered as an image rather than containing real embedded
text. Confirmed necessary for the Maerki Baumann statements specifically:
pdfplumber extracts 0 characters from them, but rendering the page and
running tesseract over it reads every figure correctly (verified against the
real printed closing balance -- see test_ocr_extraction.py).

Coordinate space: OCR pixel bounding boxes are converted to PDF points
(72 points/inch) so the SAME BANK_PROFILES column bounds and the SAME
_cluster_rows/_text helpers in statement_converter.py work completely
unmodified, whether a page's words came from the text layer or from OCR.
This module deliberately does not know anything about bank statement
structure -- it only turns pixels into words at the right coordinates.

Requires the `tesseract-ocr` binary, `pytesseract`, and `pdf2image` (which
needs `poppler-utils` for pdftoppm). These are NOT hard dependencies of
statement_converter.py -- the import is deferred until a page actually has
no text layer, so parsing any of the nine already-supported banks (all of
which have real text layers) never touches this module or requires these
packages to be installed.

DPI default is 300: enough for tesseract to read statement-quality print
correctly in testing against a real sample. This is not a universal claim
about scan quality -- a noisier scan may need a higher DPI or image
preprocessing (deskew, contrast) that isn't implemented here.
"""
from __future__ import annotations

from typing import Any


def ocr_words_for_page(pdf_path: str, page_number: int, dpi: int = 300, lang: str = "eng") -> list[dict[str, Any]]:
    """OCR one 1-indexed page of `pdf_path` and return words shaped like
    pdfplumber's extract_words(): a list of {"text", "x0", "top"} dicts in
    PDF points, top-left origin -- a drop-in replacement so the rest of the
    parsing pipeline needs no changes to consume OCR output.

    `lang` follows tesseract's language codes and supports combining
    multiple scripts on one page, e.g. lang="eng+ara" for a genuinely
    bilingual statement where both scripts carry real data (as opposed to
    DIB's statements, where the Arabic is a parallel header translation and
    the transaction data itself is plain English -- see HANDOFF_v6.md).
    Requires the corresponding tesseract-ocr-<lang> package to be installed;
    raises a clear RuntimeError if the language pack is missing rather than
    silently falling back to English and mis-extracting non-Latin text.
    """
    try:
        import pdf2image
        import pytesseract
    except ImportError as exc:
        raise RuntimeError(
            "OCR fallback needs 'pytesseract' and 'pdf2image' (pip install pytesseract pdf2image), "
            "plus the 'tesseract-ocr' and 'poppler-utils' system packages."
        ) from exc

    available = _available_languages(pytesseract)
    for code in lang.split("+"):
        if code not in available:
            raise RuntimeError(
                f"Tesseract language pack '{code}' is not installed (available: {sorted(available)}). "
                f"Install it (e.g. `apt-get install tesseract-ocr-{code}`) before OCRing with lang={lang!r}."
            )

    images = pdf2image.convert_from_path(pdf_path, dpi=dpi, first_page=page_number, last_page=page_number)
    if not images:
        return []
    image = images[0]
    scale = 72.0 / dpi  # pixels -> PDF points, matching pdfplumber's coordinate space

    data = pytesseract.image_to_data(image, lang=lang, output_type=pytesseract.Output.DICT)
    words: list[dict[str, Any]] = []
    for i, text in enumerate(data["text"]):
        text = text.strip()
        if not text:
            continue
        try:
            confidence = float(data["conf"][i])
        except (TypeError, ValueError):
            confidence = -1.0
        if confidence < 0:
            # Tesseract emits conf=-1 for structural (non-word, e.g. block/
            # paragraph/line) boxes mixed into the same flat arrays -- skip
            # those, keep only actual recognized words.
            continue
        words.append({
            "text": text,
            "x0": data["left"][i] * scale,
            "top": data["top"][i] * scale,
            "confidence": confidence,
        })
    return words


def _available_languages(pytesseract_module) -> set[str]:
    try:
        return set(pytesseract_module.get_languages(config=""))
    except Exception:
        return set()
