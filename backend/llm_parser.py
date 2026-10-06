"""Automatic LLM-based fallback for statements the heuristic parser can't
read confidently. Tier 3 of the three-tier extraction plan:

  1. Hand-built BANK_PROFILES entry (statement_converter.py)  -- highest trust
  2. Statistical column-detection (heuristic_parser.py)        -- free, private
  3. This module                                               -- LLM fallback

Two interchangeable providers, chosen by LLM_PROVIDER (see app/config.py):

  * "openai_compat" (default) -- any server exposing an OpenAI-style
    /chat/completions endpoint: a self-hosted Ollama or llama.cpp server
    (free, data never leaves your machine) or a free-tier hosted API such as
    Groq, OpenRouter or GitHub Models. Most open models cannot read a PDF
    directly, so the PDF's text layer is extracted with pdfplumber, split
    into chunks that fit a small context window, and sent as plain text.
    Scanned PDFs (no text layer) are rejected with a clear error.
  * "anthropic" -- the original behaviour: the PDF is sent to Anthropic's
    API as a native document block. Optional; costs money per call.

If you use a hosted provider, a statement's text is sent to that third party,
so the Privacy Policy must say so. A self-hosted endpoint sends nothing out.

needs_review=True is unconditional on every row this module produces,
whichever provider is used -- an LLM reading an unfamiliar layout has earned
no more trust than a statistical guess has. Weaker free models make that rule
matter more, not less. Rows with no valid date are never dropped or guessed:
the whole extraction fails loudly instead.
"""
from __future__ import annotations

import base64
import json
import re
from datetime import date
from decimal import Decimal
from typing import Any

import httpx
import pdfplumber

_API_URL = "https://api.anthropic.com/v1/messages"
_DEFAULT_MODEL = "claude-sonnet-4-6"

_PROMPT = """You are extracting transactions from a bank statement PDF for an accounting tool. Read every transaction row in this document, across all pages, and return ONLY a JSON array (no markdown fences, no commentary before or after) where each element has exactly these fields:

{"date": "YYYY-MM-DD", "description": "the transaction description text", "debit": <number or null>, "credit": <number or null>, "balance": <number or null>}

Rules:
- date must be ISO format (YYYY-MM-DD). If the statement's date format is ambiguous (e.g. 03/04/2025 could be 3 April or 4 March), use the convention that keeps dates in chronological order with the rest of the statement.
- debit and credit are never both non-null for the same row. Use null (not 0) for whichever one doesn't apply.
- balance is the running balance printed on that row, if shown. Use null if this statement doesn't print a running balance for that row.
- Do NOT include header rows, footer text, page numbers, legal notices, branch/account metadata, or summary/totals rows as transactions.
- Do NOT invent transactions that aren't printed, and do NOT skip any that are.
- Return every transaction from every page, in the order they appear.

Return ONLY the JSON array."""

_TEXT_PROMPT = """You are extracting transactions from the text of a bank statement for an accounting tool. The text below is {position} of the statement. Columns are separated by " | " where the original had wide gaps. Return ONLY a JSON array (no markdown fences, no commentary) where each element has exactly these fields:

{{"date": "YYYY-MM-DD", "description": "the transaction description text", "debit": <number or null>, "credit": <number or null>, "balance": <number or null>}}

Rules:
- date must be ISO format (YYYY-MM-DD). If the format is ambiguous (03/04/2025), choose the convention that keeps dates in chronological order.
- debit and credit are never both non-null for one row; use null (not 0) for the one that doesn't apply.
- When a running balance is printed, use it to decide which is which: the balance going DOWN means the amount is a debit, going UP means a credit. Amounts are plain numbers without currency symbols or thousands separators.
- balance is the running balance printed on that row, or null if none is printed.
- A transaction's description may continue on following lines; append those lines to its description.
- Do NOT include headers, footers, page numbers, legal notices, account details, opening/closing balance lines, or totals as transactions.
- Do NOT invent transactions and do NOT skip any that are printed.
- If this text contains no transactions, return [].

STATEMENT TEXT:
{text}

Return ONLY the JSON array."""


class LLMExtractionError(RuntimeError):
    """Raised when the LLM call fails or its response can't be trusted. The
    caller should treat this like column_detection_failed from the heuristic
    path -- tell the user this statement couldn't be read automatically,
    never silently produce an empty result and mark the statement completed."""


def _extract_json_array(text: str) -> list[dict[str, Any]]:
    # Models sometimes wrap JSON in ```json fences, or (smaller models
    # especially) add a sentence before/after it. Tolerate both rather than
    # fail, but never accept anything that isn't a list of objects.
    stripped = re.sub(r"^```(?:json)?\s*|\s*```$", "", text.strip())
    try:
        data = json.loads(stripped)
    except json.JSONDecodeError as exc:
        start, end = stripped.find("["), stripped.rfind("]")
        if start == -1 or end <= start:
            raise LLMExtractionError(f"Model response was not valid JSON: {exc}") from exc
        try:
            data = json.loads(stripped[start : end + 1])
        except json.JSONDecodeError as exc2:
            raise LLMExtractionError(f"Model response was not valid JSON: {exc2}") from exc2
    if isinstance(data, dict) and isinstance(data.get("transactions"), list):
        data = data["transactions"]  # some models wrap the array in an object
    if not isinstance(data, list):
        raise LLMExtractionError("Model response was valid JSON but not a list of transactions.")
    if not all(isinstance(item, dict) for item in data):
        raise LLMExtractionError("Model response contained non-object entries in the transaction list.")
    return data


def _to_decimal(value: Any) -> Decimal | None:
    if value is None:
        return None
    if isinstance(value, str):
        value = value.replace(",", "").strip()
        if not value:
            return None
    number = Decimal(str(value))
    if not number.is_finite():
        raise ValueError("non-finite amount")
    return number


_ISO_DATE = re.compile(r"^\d{4}-\d{2}-\d{2}$")


def _build_result(raw_transactions: list[dict[str, Any]]) -> dict[str, Any]:
    """Shared by every provider: validate rows, run the balance-chain
    confidence pass, and force needs_review=True."""
    if not raw_transactions:
        raise LLMExtractionError("The model returned no transactions for this statement.")

    prior_balance: Decimal | None = None
    checked = 0
    matched = 0
    result: list[dict[str, Any]] = []
    bad_dates: list[Any] = []
    for row in raw_transactions:
        try:
            debit = _to_decimal(row.get("debit"))
            credit = _to_decimal(row.get("credit"))
            balance = _to_decimal(row.get("balance"))
        except Exception as exc:  # malformed number from the model
            raise LLMExtractionError(f"Malformed amount in model response: {row!r}") from exc

        raw_date = row.get("date")
        try:
            if not isinstance(raw_date, str) or not _ISO_DATE.match(raw_date):
                raise ValueError
            date.fromisoformat(raw_date)
        except ValueError:
            bad_dates.append(raw_date)

        if balance is not None and prior_balance is not None:
            checked += 1
            if abs((prior_balance - (debit or Decimal("0")) + (credit or Decimal("0"))) - balance) <= Decimal("0.01"):
                matched += 1
        result.append({
            "date": raw_date,
            "description": str(row.get("description") or "").strip(),
            "debit": float(debit) if debit is not None else None,
            "credit": float(credit) if credit is not None else None,
            "balance": float(balance) if balance is not None else None,
            "needs_review": True,  # unconditional -- see module docstring
        })
        if balance is not None:
            prior_balance = balance

    if bad_dates:
        raise LLMExtractionError(
            f"{len(bad_dates)} of {len(result)} rows had no valid YYYY-MM-DD date "
            f"(e.g. {bad_dates[0]!r}); refusing to drop or guess them."
        )

    return {
        "transactions": result,
        "confidence": (matched / checked) if checked else None,
        "extraction_method": "llm",
    }


# --------------------------------------------------------------------------
# Provider: Anthropic (native PDF document block) -- optional
# --------------------------------------------------------------------------

def parse_statement_llm(
    pdf_path: str,
    api_key: str,
    model: str = _DEFAULT_MODEL,
    timeout: float = 120.0,
) -> dict[str, Any]:
    """Send the PDF directly to Claude's API and parse its JSON response.
    Raises LLMExtractionError on any failure."""
    with open(pdf_path, "rb") as f:
        pdf_b64 = base64.standard_b64encode(f.read()).decode("ascii")

    response = httpx.post(
        _API_URL,
        headers={
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        },
        json={
            "model": model,
            "max_tokens": 8192,
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {"type": "document", "source": {"type": "base64", "media_type": "application/pdf", "data": pdf_b64}},
                        {"type": "text", "text": _PROMPT},
                    ],
                }
            ],
        },
        timeout=timeout,
    )
    if response.status_code != 200:
        raise LLMExtractionError(f"Anthropic API returned {response.status_code}: {response.text[:500]}")

    body = response.json()
    text_blocks = [block["text"] for block in body.get("content", []) if block.get("type") == "text"]
    if not text_blocks:
        raise LLMExtractionError("Model response contained no text content.")

    return _build_result(_extract_json_array("".join(text_blocks)))


# --------------------------------------------------------------------------
# Provider: any OpenAI-compatible endpoint (Ollama, llama.cpp, Groq, ...)
# --------------------------------------------------------------------------

def _pdf_text_chunks(pdf_path: str, max_chars: int) -> list[str]:
    """Extract the PDF's text layer as layout-preserving lines and split it
    into chunks of at most ~max_chars, so each fits a small model's context.
    A transaction whose description wraps across a chunk boundary can lose
    its tail -- amounts and dates sit on the first line, so they survive."""
    lines: list[str] = []
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            text = page.extract_text(layout=True) or ""
            for line in text.splitlines():
                if line.strip():
                    # Wide layout padding wastes tokens; keep a visible
                    # column-gap marker instead.
                    lines.append(re.sub(r" {3,}", " | ", line.strip()))
    if not lines:
        raise LLMExtractionError(
            "This PDF has no text layer (it looks scanned), so a text-only model cannot read it."
        )

    chunks: list[str] = []
    current: list[str] = []
    size = 0
    for line in lines:
        if current and size + len(line) + 1 > max_chars:
            chunks.append("\n".join(current))
            current, size = [], 0
        current.append(line)
        size += len(line) + 1
    if current:
        chunks.append("\n".join(current))
    return chunks


def _chat_completion(base_url: str, model: str, api_key: str | None, prompt: str, timeout: float) -> str:
    url = base_url.rstrip("/") + "/chat/completions"
    headers = {"content-type": "application/json"}
    if api_key:
        headers["authorization"] = f"Bearer {api_key}"
    try:
        response = httpx.post(
            url,
            headers=headers,
            json={
                "model": model,
                "temperature": 0,
                "max_tokens": 4096,
                "messages": [{"role": "user", "content": prompt}],
            },
            timeout=timeout,
        )
    except httpx.HTTPError as exc:
        raise LLMExtractionError(f"Could not reach the LLM endpoint at {base_url}: {exc}") from exc
    if response.status_code != 200:
        raise LLMExtractionError(f"LLM endpoint returned {response.status_code}: {response.text[:500]}")
    try:
        choice = response.json()["choices"][0]
        content = choice["message"]["content"]
    except (KeyError, IndexError, TypeError, ValueError) as exc:
        raise LLMExtractionError("LLM endpoint returned an unexpected response shape.") from exc
    if choice.get("finish_reason") == "length":
        raise LLMExtractionError(
            "The model's output was cut off before it finished; lower LLM_CHUNK_CHARS or use a model with a larger output limit."
        )
    if not isinstance(content, str) or not content.strip():
        raise LLMExtractionError("LLM endpoint returned an empty response.")
    return content


def parse_statement_llm_text(
    pdf_path: str,
    base_url: str,
    model: str,
    api_key: str | None = None,
    timeout: float = 300.0,
    chunk_chars: int = 6000,
) -> dict[str, Any]:
    """Text-only extraction through an OpenAI-compatible chat endpoint."""
    chunks = _pdf_text_chunks(pdf_path, chunk_chars)
    rows: list[dict[str, Any]] = []
    for index, chunk in enumerate(chunks):
        if len(chunks) == 1:
            position = "the whole text"
        else:
            position = f"part {index + 1} of {len(chunks)} (it may start or end mid-transaction)"
        prompt = _TEXT_PROMPT.format(position=position, text=chunk)
        rows.extend(_extract_json_array(_chat_completion(base_url, model, api_key, prompt, timeout)))
    return _build_result(rows)


# --------------------------------------------------------------------------
# Entry point used by app/main.py
# --------------------------------------------------------------------------

def parse_statement_llm_configured(pdf_path: str, settings: Any) -> dict[str, Any]:
    """Run whichever provider `settings.llm_provider` selects. Takes the
    Settings object (duck-typed) so main.py stays provider-agnostic."""
    provider = (getattr(settings, "llm_provider", None) or "openai_compat").strip().lower()
    if provider == "anthropic":
        key = getattr(settings, "anthropic_api_key", None)
        if not key:
            raise LLMExtractionError("LLM_PROVIDER=anthropic but ANTHROPIC_API_KEY is not set.")
        return parse_statement_llm(pdf_path, key)
    if provider == "openai_compat":
        model = getattr(settings, "llm_model", None)
        if not model:
            raise LLMExtractionError(
                "No LLM is configured. Set LLM_MODEL (and LLM_BASE_URL) to an Ollama or other OpenAI-compatible endpoint."
            )
        return parse_statement_llm_text(
            pdf_path,
            base_url=getattr(settings, "llm_base_url", "http://localhost:11434/v1"),
            model=model,
            api_key=getattr(settings, "llm_api_key", None),
            timeout=getattr(settings, "llm_timeout_seconds", 300.0),
            chunk_chars=getattr(settings, "llm_chunk_chars", 6000),
        )
    raise LLMExtractionError(f"Unknown LLM_PROVIDER {provider!r}; use 'openai_compat' or 'anthropic'.")
