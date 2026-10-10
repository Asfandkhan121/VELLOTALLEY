from __future__ import annotations

import logging
from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import Any, Callable
from uuid import UUID, uuid4

from fastapi import Depends, FastAPI, File, Form, HTTPException, Response, UploadFile, status
from starlette.background import BackgroundTask
from fastapi.responses import FileResponse
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from excel_export import export_to_excel
from statement_converter import BANK_PROFILES, parse_statement
from heuristic_parser import parse_statement_heuristic
from llm_parser import parse_statement_llm_configured, LLMExtractionError

from nlp import TransactionInput, analyze_transactions

from .config import Settings
from .repository import SupabaseRepository, month_start_now


bearer_scheme = HTTPBearer(auto_error=False)
logger = logging.getLogger(__name__)


def _should_use_llm_fallback(heuristic_result: dict[str, Any]) -> bool:
    """Missing balance confidence is not low extraction confidence."""
    confidence = heuristic_result["confidence"]
    return heuristic_result["column_detection_failed"] or (
        confidence is not None and confidence < 0.85
    )


def create_app(settings: Settings | None = None, repository: Any | None = None) -> FastAPI:
    app = FastAPI(title="Vellotalley API", version="0.1.0")
    runtime_settings = settings or Settings.from_environment()
    repo = repository or SupabaseRepository(runtime_settings)

    def current_user(credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme)) -> str:
        if credentials is None or credentials.scheme.lower() != "bearer":
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Bearer authentication is required.")
        try:
            return repo.authenticate(credentials.credentials)
        except Exception as exc:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired access token.") from exc

    @app.post("/v1/clients", status_code=status.HTTP_201_CREATED)
    def create_client(name: str = Form(...), user_id: str = Depends(current_user)) -> dict[str, Any]:
        stripped = name.strip()
        if not stripped:
            raise HTTPException(status_code=422, detail="Client name must not be empty.")
        return repo.create_client(user_id, stripped)

    @app.get("/v1/clients")
    def list_clients(user_id: str = Depends(current_user)) -> list[dict[str, Any]]:
        return repo.list_clients(user_id)

    @app.get("/v1/account-heads")
    def list_account_heads(user_id: str = Depends(current_user)) -> list[dict[str, Any]]:
        # Global reference data (not per-user); auth is still required.
        return repo.list_account_heads()

    @app.delete("/v1/account", status_code=status.HTTP_204_NO_CONTENT, response_class=Response)
    def delete_account(user_id: str = Depends(current_user)) -> Response:
        try:
            repo.delete_account(user_id)
        except Exception as exc:
            logger.error("Account deletion failed with %s.", type(exc).__name__)
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="Account deletion could not be completed. Some data may already have been removed. Contact HELP@VELLOTALLEY.COM before retrying.",
            ) from exc
        return Response(status_code=status.HTTP_204_NO_CONTENT)

    @app.post("/v1/statements", status_code=status.HTTP_201_CREATED)
    async def upload_statement(
        client_id: UUID = Form(...), bank_profile: str = Form(...), file: UploadFile = File(...), user_id: str = Depends(current_user),
    ) -> dict[str, Any]:
        profile = bank_profile.lower()
        if profile != "auto" and profile not in BANK_PROFILES:
            try:
                repo.log_demand_signal(user_id, profile)
            except Exception:
                pass  # a logging hiccup must never block or corrupt the real error response
            raise HTTPException(status_code=422, detail=f"Unsupported bank profile. Choose from: {', '.join(BANK_PROFILES)}, or 'auto' for an unlisted bank.")
        if not file.filename or not file.filename.lower().endswith(".pdf"):
            raise HTTPException(status_code=415, detail="Only PDF statement uploads are accepted.")
        content = await file.read()
        if not _looks_like_pdf(content):
            raise HTTPException(status_code=415, detail="The upload is not a valid PDF file.")
        if not repo.client_belongs_to_user(client_id, user_id):
            raise HTTPException(status_code=404, detail="Client not found.")
        if (
            user_id.lower() not in runtime_settings.unlimited_conversion_user_ids
            and repo.monthly_conversion_count(user_id, month_start_now()) >= runtime_settings.free_monthly_limit
        ):
            raise HTTPException(status_code=429, detail="Free-tier limit reached: three conversions per calendar month.")

        statement_id = uuid4()
        try:
            repo.upload_pdf(user_id, statement_id, content)
            statement = repo.create_statement(statement_id=statement_id, client_id=client_id, user_id=user_id, original_filename=Path(file.filename).name, bank_profile=profile)
        except Exception as exc:
            raise HTTPException(status_code=502, detail="Could not store the statement.") from exc
        return statement

    def _run_extraction(statement_id: UUID, user_id: str, statement: dict[str, Any]) -> dict[str, Any]:
        """Shared by /extract (first attempt, requires status=processing) and
        /retry (requires status=failed) -- the actual extraction logic
        doesn't care which state it was called from, only the endpoints'
        status-guards differ."""
        source_path: str | None = None
        try:
            with NamedTemporaryFile(suffix=".pdf", delete=False) as source:
                source.write(repo.download_pdf(user_id, statement_id))
                source_path = source.name
            if statement["bank_profile"] == "auto":
                heuristic_result = parse_statement_heuristic(source_path)
                if _should_use_llm_fallback(heuristic_result):
                    try:
                        llm_result = parse_statement_llm_configured(source_path, runtime_settings)
                    except LLMExtractionError as exc:
                        repo.set_statement_status(statement_id, user_id, "failed")
                        raise HTTPException(status_code=422, detail=f"Could not read this statement automatically: {exc}") from exc
                    transactions = llm_result["transactions"]
                    extra = {"extraction_method": "llm", "confidence": llm_result["confidence"]}
                else:
                    transactions = heuristic_result["transactions"]
                    extra = {
                        "extraction_method": "heuristic",
                        "layout_detected": heuristic_result["layout_detected"],
                        "confidence": heuristic_result["confidence"],
                        "date_format_ambiguous": heuristic_result["date_format_ambiguous"],
                    }
            else:
                transactions = parse_statement(source_path, statement["bank_profile"])
                extra = {"extraction_method": "profile"}
            if not transactions:
                repo.set_statement_status(statement_id, user_id, "failed")
                raise HTTPException(
                    status_code=422,
                    detail="No transactions could be extracted from this statement.",
                )
            # Idempotent: a retry after a partial failure (or a plain repeat
            # call) must never leave duplicate rows behind.
            repo.delete_transactions(statement_id)
            repo.insert_transactions(statement_id, transactions)
            repo.set_statement_status(
                statement_id, user_id, "completed",
                extraction_method=extra.get("extraction_method"), confidence=extra.get("confidence"),
            )
            return {
                "statement_id": str(statement_id),
                "transactions": _transactions_with_nlp_insights(_json_transactions(transactions)),
                **extra,
            }
        except HTTPException:
            raise
        except Exception as exc:
            repo.set_statement_status(statement_id, user_id, "failed")
            raise HTTPException(status_code=422, detail="Statement extraction failed.") from exc
        finally:
            if source_path:
                Path(source_path).unlink(missing_ok=True)

    @app.post("/v1/statements/{statement_id}/extract")
    def extract_statement(statement_id: UUID, user_id: str = Depends(current_user)) -> dict[str, Any]:
        statement = _owned_statement(repo, statement_id, user_id)
        if statement["status"] != "processing":
            raise HTTPException(status_code=409, detail="Only statements in processing status can be extracted.")
        return _run_extraction(statement_id, user_id, statement)

    @app.post("/v1/statements/{statement_id}/retry")
    def retry_statement(statement_id: UUID, user_id: str = Depends(current_user)) -> dict[str, Any]:
        statement = _owned_statement(repo, statement_id, user_id)
        if statement["status"] != "failed":
            raise HTTPException(status_code=409, detail="Only statements in failed status can be retried.")
        return _run_extraction(statement_id, user_id, statement)

    @app.get("/v1/statements")
    def list_statements(user_id: str = Depends(current_user)) -> list[dict[str, Any]]:
        return repo.list_statements(user_id)

    @app.get("/v1/statements/{statement_id}")
    def get_statement(statement_id: UUID, user_id: str = Depends(current_user)) -> dict[str, Any]:
        return _owned_statement(repo, statement_id, user_id)

    @app.get("/v1/statements/{statement_id}/transactions")
    def get_transactions(statement_id: UUID, user_id: str = Depends(current_user)) -> list[dict[str, Any]]:
        _owned_statement(repo, statement_id, user_id)
        return _transactions_with_nlp_insights(_json_transactions(repo.get_transactions(statement_id)))

    @app.get("/v1/statements/{statement_id}/excel")
    def download_excel(statement_id: UUID, user_id: str = Depends(current_user)) -> FileResponse:
        _owned_statement(repo, statement_id, user_id)
        transactions = repo.get_transactions(statement_id)
        if not transactions:
            raise HTTPException(status_code=409, detail="No extracted transactions are available for this statement.")
        output_path = Path(NamedTemporaryFile(suffix=".xlsx", delete=False).name)
        export_to_excel(transactions, str(output_path))
        return FileResponse(
            output_path,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            filename=f"statement-{statement_id}.xlsx",
            background=BackgroundTask(output_path.unlink, missing_ok=True),
        )

    @app.post("/v1/statements/{statement_id}/notes", status_code=status.HTTP_201_CREATED)
    def add_note(statement_id: UUID, note: str = Form(...), user_id: str = Depends(current_user)) -> dict[str, Any]:
        """Store a free-text note against a statement -- a correction, a
        reminder about that bank's quirks, or an instruction for next time.

        This does NOT feed back into parsing automatically. Notes are data
        for a human to read and act on (e.g. when refining a bank profile's
        coordinates), not something the parser reads and self-modifies
        from -- see HANDOFF_v10.md for why that boundary is deliberate.
        """
        _owned_statement(repo, statement_id, user_id)
        stripped = note.strip()
        if not stripped:
            raise HTTPException(status_code=422, detail="Note must not be empty.")
        if len(stripped) > 2000:
            raise HTTPException(status_code=422, detail="Note must be 2000 characters or fewer.")
        return repo.add_note(statement_id, user_id, stripped)

    @app.get("/v1/statements/{statement_id}/notes")
    def list_notes(statement_id: UUID, user_id: str = Depends(current_user)) -> list[dict[str, Any]]:
        _owned_statement(repo, statement_id, user_id)
        return repo.list_notes(statement_id, user_id)

    return app


def _owned_statement(repo: Any, statement_id: UUID, user_id: str) -> dict[str, Any]:
    statement = repo.get_statement(statement_id, user_id)
    if statement is None:
        raise HTTPException(status_code=404, detail="Statement not found.")
    return statement


def _looks_like_pdf(content: bytes) -> bool:
    return content.lstrip(b"\xef\xbb\xbf\x00\t\r\n ").startswith(b"%PDF-")


def _json_transactions(transactions: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [{**item, **{field: (None if item[field] is None else f"{item[field]:.2f}") for field in ("debit", "credit", "balance")}} for item in transactions]


def _transactions_with_nlp_insights(transactions: list[dict[str, Any]]) -> list[dict[str, Any]]:
    analyses = analyze_transactions([
        TransactionInput(description=item.get("description") or "", date=item.get("date"))
        for item in transactions
    ])
    return [
        {
            **transaction,
            "nlp_insight": {
                "decision": analysis.decision.value,
                "method": analysis.method.value,
                "normalized_description": analysis.normalized_description,
                "rule_label": analysis.rule_label,
                "rule_confidence": analysis.rule_confidence,
                "fuzzy_match_text": analysis.fuzzy_match_text,
                "fuzzy_similarity": analysis.fuzzy_similarity,
                "review_reasons": analysis.review_reasons,
            },
        }
        for transaction, analysis in zip(transactions, analyses, strict=True)
    ]


def app_factory() -> FastAPI:
    """Uvicorn factory that reads server-only configuration at process start.

    Keeping construction here (rather than at import time) means test suites can
    import ``create_app`` and supply an in-memory repository without needing a
    real-shaped Supabase secret.
    """
    return create_app()
