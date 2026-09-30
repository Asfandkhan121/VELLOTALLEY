"""Automatic LLM-based fallback for statements the heuristic parser can't
read confidently -- no manual "try harder" step, no per-use consent click.
This is the second, last-resort tier of the three-tier extraction plan
recorded in PRODUCT_VISION_AND_ROADMAP.md:

  1. Hand-built BANK_PROFILES entry (statement_converter.py)  -- highest trust
  2. Statistical column-detection (heuristic_parser.py)        -- free, private
  3. This module                                               -- automatic,
     costs money per call, sends the real PDF to Anthropic's API

Because tier 3 fires automatically now rather than behind a user-facing
consent click, put a plain-language line in your product's Privacy Policy /
Terms of Service saying that a statement may be sent to a third-party AI
provider for processing when it can't be read automatically -- a one-time
disclosure there, not a per-upload prompt, is the right level for this now.

needs_review=True is still unconditional on every row this module produces,
exactly like heuristic_parser.py -- an LLM reading an unfamiliar layout has
earned no more trust than a statistical guess has, and the standing rule
("no exceptions") doesn't change just because the trigger for using this
path changed from a manual click to an automatic threshold.
"""
from __future__ import annotations

import base64
import json
import re
from decimal import Decimal
from typing import Any

import httpx

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


class LLMExtractionError(RuntimeError):
    """Raised when the API call fails or the model's response can't be
    parsed as the expected JSON shape. The caller should treat this exactly
    like column_detection_failed from the heuristic path -- tell the user
    this statement couldn't be read automatically, don't silently produce
    an empty result and mark the statement completed."""


def _extract_json_array(text: str) -> list[dict[str, Any]]:
    # Models sometimes wrap JSON in ```json fences despite instructions not
    # to -- strip that defensively rather than fail on it.
    stripped = re.sub(r"^```(?:json)?\s*|\s*```$", "", text.strip())
    try:
        data = json.loads(stripped)
    except json.JSONDecodeError as exc:
        raise LLMExtractionError(f"Model response was not valid JSON: {exc}") from exc
    if not isinstance(data, list):
        raise LLMExtractionError("Model response was valid JSON but not a list of transactions.")
    return data


def parse_statement_llm(
    pdf_path: str,
    api_key: str,
    model: str = _DEFAULT_MODEL,
    timeout: float = 120.0,
) -> dict[str, Any]:
    """Send the PDF directly to Claude's API (no page-to-image conversion
    needed -- the API accepts a PDF document content block natively) and
    parse its structured-JSON response into the same transaction shape the
    other two parsers produce.

    Returns:
    {
      "transactions": [...],   # each item always has needs_review=True
      "confidence": float | None,  # balance-chain match rate, same meaning as heuristic_parser's
      "extraction_method": "llm",
    }
    Raises LLMExtractionError on any failure -- the caller should surface
    this as "couldn't read this statement automatically", not swallow it
    into an empty successful result.
    """
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

    raw_transactions = _extract_json_array("".join(text_blocks))

    # Same balance-chain confidence pass as heuristic_parser.py, for the
    # same reason: an LLM's read of an unfamiliar layout is still a guess,
    # and this is how much of that guess independently checks out.
    prior_balance: Decimal | None = None
    checked = 0
    matched = 0
    result: list[dict[str, Any]] = []
    for row in raw_transactions:
        try:
            debit = Decimal(str(row["debit"])) if row.get("debit") is not None else None
            credit = Decimal(str(row["credit"])) if row.get("credit") is not None else None
            balance = Decimal(str(row["balance"])) if row.get("balance") is not None else None
        except Exception as exc:  # malformed number from the model
            raise LLMExtractionError(f"Malformed amount in model response: {row!r}") from exc

        if balance is not None and prior_balance is not None:
            checked += 1
            if abs((prior_balance - (debit or Decimal("0")) + (credit or Decimal("0"))) - balance) <= Decimal("0.01"):
                matched += 1
        result.append({
            "date": row.get("date"),
            "description": (row.get("description") or "").strip(),
            "debit": float(debit) if debit is not None else None,
            "credit": float(credit) if credit is not None else None,
            "balance": float(balance) if balance is not None else None,
            "needs_review": True,  # unconditional -- see module docstring
        })
        if balance is not None:
            prior_balance = balance

    return {
        "transactions": result,
        "confidence": (matched / checked) if checked else None,
        "extraction_method": "llm",
    }
