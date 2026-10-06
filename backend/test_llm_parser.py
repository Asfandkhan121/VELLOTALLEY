"""Tests for llm_parser.py's provider-agnostic text path.

The HTTP layer is mocked, so these prove the plumbing (chunking, JSON
tolerance, validation, the unconditional needs_review rule, config dispatch).
They do NOT prove any real model reads a real statement accurately -- that
needs a run against a live Ollama/hosted model and real PDFs.
"""
import json
from types import SimpleNamespace

import httpx
import pytest

import llm_parser
from llm_parser import LLMExtractionError


def make_pdf(path, lines):
    """Hand-build a minimal one-page text PDF (no extra dependencies)."""
    content = "BT /F1 10 Tf 12 TL 20 780 Td\n" + "\n".join(f"({l}) '" for l in lines) + "\nET"
    objs = [
        "<< /Type /Catalog /Pages 2 0 R >>",
        "<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
        "<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Contents 4 0 R /Resources << /Font << /F1 5 0 R >> >> >>",
        f"<< /Length {len(content)} >>\nstream\n{content}\nendstream",
        "<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
    ]
    out, offsets = "%PDF-1.4\n", []
    for i, body in enumerate(objs, 1):
        offsets.append(len(out))
        out += f"{i} 0 obj\n{body}\nendobj\n"
    xref = len(out)
    out += f"xref\n0 {len(objs)+1}\n0000000000 65535 f \n" + "".join(f"{o:010d} 00000 n \n" for o in offsets)
    out += f"trailer\n<< /Size {len(objs)+1} /Root 1 0 R >>\nstartxref\n{xref}\n%%EOF"
    path.write_bytes(out.encode("latin-1"))


def fake_post(reply, status=200, finish="stop"):
    calls = []

    def _post(url, headers=None, json=None, timeout=None):
        calls.append({"url": url, "headers": headers, "json": json})
        body = {"choices": [{"message": {"content": reply}, "finish_reason": finish}]}
        return httpx.Response(status, json=body, request=httpx.Request("POST", url))

    _post.calls = calls
    return _post


ROWS = [
    {"date": "2025-01-02", "description": "Opening deposit", "debit": None, "credit": "1,000.00", "balance": 1000.0},
    {"date": "2025-01-03", "description": "ATM", "debit": 200, "credit": None, "balance": 800.0},
]


def test_text_pdf_roundtrip_and_rules(tmp_path, monkeypatch):
    pdf = tmp_path / "s.pdf"
    make_pdf(pdf, ["Date      Description      Debit      Credit      Balance", "02-01-2025   Opening deposit   1,000.00   1,000.00"])
    post = fake_post(json.dumps(ROWS))
    monkeypatch.setattr(llm_parser.httpx, "post", post)
    result = llm_parser.parse_statement_llm_text(str(pdf), "http://x/v1/", "m", api_key="k")
    assert result["extraction_method"] == "llm"
    assert all(t["needs_review"] is True for t in result["transactions"])  # unconditional
    assert result["transactions"][0]["credit"] == 1000.0  # "1,000.00" string coerced
    assert result["confidence"] == 1.0  # 1000 - 200 == 800 balance chain
    assert post.calls[0]["url"] == "http://x/v1/chat/completions"
    assert post.calls[0]["headers"]["authorization"] == "Bearer k"
    assert " | " in post.calls[0]["json"]["messages"][0]["content"]  # column-gap marker


def test_no_auth_header_without_key(tmp_path, monkeypatch):
    pdf = tmp_path / "s.pdf"; make_pdf(pdf, ["hello 02-01-2025"])
    post = fake_post(json.dumps(ROWS))
    monkeypatch.setattr(llm_parser.httpx, "post", post)
    llm_parser.parse_statement_llm_text(str(pdf), "http://localhost:11434/v1", "m")
    assert "authorization" not in post.calls[0]["headers"]


def test_multi_chunk_calls_once_per_chunk(tmp_path, monkeypatch):
    pdf = tmp_path / "s.pdf"; make_pdf(pdf, [f"row {i} 02-01-2025 100.00" for i in range(30)])
    post = fake_post(json.dumps(ROWS[:1]))
    monkeypatch.setattr(llm_parser.httpx, "post", post)
    result = llm_parser.parse_statement_llm_text(str(pdf), "http://x/v1", "m", chunk_chars=200)
    assert len(post.calls) > 1
    assert len(result["transactions"]) == len(post.calls)  # one row mocked per chunk


@pytest.mark.parametrize("reply", [
    "```json\n" + json.dumps(ROWS) + "\n```",
    "Sure! Here you go:\n" + json.dumps(ROWS) + "\nHope that helps.",
    json.dumps({"transactions": ROWS}),
])
def test_json_tolerance(reply):
    assert len(llm_parser._extract_json_array(reply)) == 2


@pytest.mark.parametrize("reply", ["not json at all", '"just a string"', "[1, 2]", '{"a": 1}'])
def test_json_rejects_garbage(reply):
    with pytest.raises(LLMExtractionError):
        llm_parser._extract_json_array(reply)


def test_bad_date_fails_loudly_not_silently():
    bad = ROWS + [{"date": "02/01/2025", "description": "x", "debit": 1, "credit": None, "balance": None}]
    with pytest.raises(LLMExtractionError, match="no valid YYYY-MM-DD date"):
        llm_parser._build_result(bad)


def test_missing_date_and_empty_result_rejected():
    with pytest.raises(LLMExtractionError):
        llm_parser._build_result([{"description": "x", "debit": 1}])
    with pytest.raises(LLMExtractionError, match="no transactions"):
        llm_parser._build_result([])


def test_malformed_amount_rejected():
    with pytest.raises(LLMExtractionError, match="Malformed amount"):
        llm_parser._build_result([{"date": "2025-01-02", "debit": "abc"}])
    with pytest.raises(LLMExtractionError, match="Malformed amount"):
        llm_parser._build_result([{"date": "2025-01-02", "debit": "NaN"}])


def test_truncated_output_rejected(tmp_path, monkeypatch):
    pdf = tmp_path / "s.pdf"; make_pdf(pdf, ["a 02-01-2025"])
    monkeypatch.setattr(llm_parser.httpx, "post", fake_post("[", finish="length"))
    with pytest.raises(LLMExtractionError, match="cut off"):
        llm_parser.parse_statement_llm_text(str(pdf), "http://x/v1", "m")


def test_http_error_and_unreachable(tmp_path, monkeypatch):
    pdf = tmp_path / "s.pdf"; make_pdf(pdf, ["a 02-01-2025"])
    monkeypatch.setattr(llm_parser.httpx, "post", fake_post("x", status=500))
    with pytest.raises(LLMExtractionError, match="500"):
        llm_parser.parse_statement_llm_text(str(pdf), "http://x/v1", "m")

    def boom(*a, **k):
        raise httpx.ConnectError("refused")
    monkeypatch.setattr(llm_parser.httpx, "post", boom)
    with pytest.raises(LLMExtractionError, match="Could not reach"):
        llm_parser.parse_statement_llm_text(str(pdf), "http://x/v1", "m")


def test_pdf_without_text_layer_rejected(tmp_path):
    pdf = tmp_path / "blank.pdf"; make_pdf(pdf, [])
    with pytest.raises(LLMExtractionError, match="no text layer"):
        llm_parser._pdf_text_chunks(str(pdf), 6000)


def test_dispatch_requires_model_and_known_provider():
    base = dict(llm_provider="openai_compat", llm_model=None, anthropic_api_key=None)
    with pytest.raises(LLMExtractionError, match="No LLM is configured"):
        llm_parser.parse_statement_llm_configured("x.pdf", SimpleNamespace(**base))
    with pytest.raises(LLMExtractionError, match="ANTHROPIC_API_KEY"):
        llm_parser.parse_statement_llm_configured("x.pdf", SimpleNamespace(**{**base, "llm_provider": "anthropic"}))
    with pytest.raises(LLMExtractionError, match="Unknown LLM_PROVIDER"):
        llm_parser.parse_statement_llm_configured("x.pdf", SimpleNamespace(**{**base, "llm_provider": "nope"}))


def test_dispatch_routes_to_text_path(monkeypatch):
    seen = {}
    monkeypatch.setattr(llm_parser, "parse_statement_llm_text", lambda p, **kw: seen.update(kw) or {"ok": 1})
    s = SimpleNamespace(llm_provider="openai_compat", llm_model="qwen", llm_base_url="http://h/v1",
                        llm_api_key=None, llm_timeout_seconds=9.0, llm_chunk_chars=123)
    assert llm_parser.parse_statement_llm_configured("x.pdf", s) == {"ok": 1}
    assert seen == {"base_url": "http://h/v1", "model": "qwen", "api_key": None, "timeout": 9.0, "chunk_chars": 123}
