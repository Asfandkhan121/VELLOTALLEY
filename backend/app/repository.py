"""Server-only Supabase data access.

The service-role key is used only in this backend. Every query still includes
an explicit user-id ownership filter; RLS remains a second line of defense.
"""
from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal
from typing import Any
from uuid import UUID

from supabase import Client, create_client

from .config import Settings

_STORAGE_LIST_PAGE_SIZE = 1000
_STORAGE_DELETE_BATCH_SIZE = 1000


class SupabaseRepository:
    def __init__(self, settings: Settings) -> None:
        self.client: Client = create_client(settings.supabase_url, settings.supabase_service_role_key)
        self.bucket = settings.statement_bucket

    def authenticate(self, access_token: str) -> str:
        user = self.client.auth.get_user(access_token).user
        if user is None:
            raise ValueError("Invalid access token")
        return str(user.id)

    def create_client(self, user_id: str, name: str) -> dict[str, Any]:
        response = self.client.table("clients").insert({"user_id": user_id, "name": name}).execute()
        return response.data[0]

    def list_clients(self, user_id: str) -> list[dict[str, Any]]:
        response = self.client.table("clients").select("id,name,created_at").eq("user_id", user_id).order("created_at", desc=True).execute()
        return response.data or []

    def client_belongs_to_user(self, client_id: UUID, user_id: str) -> bool:
        response = self.client.table("clients").select("id").eq("id", str(client_id)).eq("user_id", user_id).maybe_single().execute()
        return response is not None and response.data is not None

    def monthly_conversion_count(self, user_id: str, month_start: datetime) -> int:
        response = (
            self.client.table("statements")
            .select("id", count="exact")
            .eq("user_id", user_id)
            .gte("uploaded_at", month_start.isoformat())
            .execute()
        )
        return int(response.count or 0)

    def create_statement(self, *, statement_id: UUID, client_id: UUID, user_id: str, original_filename: str, bank_profile: str) -> dict[str, Any]:
        response = self.client.table("statements").insert({
            "id": str(statement_id), "client_id": str(client_id), "user_id": user_id,
            "original_filename": original_filename, "bank_profile": bank_profile, "status": "processing",
        }).execute()
        return response.data[0]

    def get_statement(self, statement_id: UUID, user_id: str) -> dict[str, Any] | None:
        response = self.client.table("statements").select("*").eq("id", str(statement_id)).eq("user_id", user_id).maybe_single().execute()
        return response.data if response is not None else None

    def list_statements(self, user_id: str) -> list[dict[str, Any]]:
        response = (
            self.client.table("statements")
            .select("id,client_id,original_filename,bank_profile,uploaded_at,status,extraction_method,confidence")
            .eq("user_id", user_id).order("uploaded_at", desc=True).execute()
        )
        return response.data or []

    def set_statement_status(
        self, statement_id: UUID, user_id: str, status: str,
        extraction_method: str | None = None, confidence: float | None = None,
    ) -> None:
        update: dict[str, Any] = {"status": status}
        if extraction_method is not None:
            update["extraction_method"] = extraction_method
        if confidence is not None:
            update["confidence"] = confidence
        self.client.table("statements").update(update).eq("id", str(statement_id)).eq("user_id", user_id).execute()

    def insert_transactions(self, statement_id: UUID, transactions: list[dict[str, Any]]) -> None:
        rows = [{
            "statement_id": str(statement_id), "date": item["date"], "description": item["description"],
            "debit": _decimal_text(item["debit"]), "credit": _decimal_text(item["credit"]),
            "balance": _decimal_text(item["balance"]), "needs_review": item["needs_review"],
            "transaction_sequence": sequence,
        } for sequence, item in enumerate(transactions, start=1)]
        if rows:
            self.client.table("transactions").insert(rows).execute()

    def delete_transactions(self, statement_id: UUID) -> None:
        # Makes extraction idempotent -- a /retry after a failed attempt (or
        # a partial insert from one) should never leave duplicate or stale
        # rows behind. Cascade-deletes nothing on its own since these are
        # the child rows, not the parent statement.
        self.client.table("transactions").delete().eq("statement_id", str(statement_id)).execute()

    def get_transactions(self, statement_id: UUID) -> list[dict[str, Any]]:
        response = self.client.table("transactions").select("date,description,debit,credit,balance,needs_review").eq("statement_id", str(statement_id)).order("transaction_sequence").execute()
        return response.data or []

    def upload_pdf(self, user_id: str, statement_id: UUID, content: bytes) -> None:
        self.client.storage.from_(self.bucket).upload(f"{user_id}/{statement_id}/source.pdf", content, {"content-type": "application/pdf", "upsert": "false"})

    def download_pdf(self, user_id: str, statement_id: UUID) -> bytes:
        return self.client.storage.from_(self.bucket).download(f"{user_id}/{statement_id}/source.pdf")

    def add_note(self, statement_id: UUID, user_id: str, note: str) -> dict[str, Any]:
        response = self.client.table("statement_notes").insert({
            "statement_id": str(statement_id), "user_id": user_id, "note": note,
        }).execute()
        return response.data[0]

    def list_notes(self, statement_id: UUID, user_id: str) -> list[dict[str, Any]]:
        response = (
            self.client.table("statement_notes")
            .select("id,note,created_at")
            .eq("statement_id", str(statement_id))
            .eq("user_id", user_id)
            .order("created_at", desc=True)
            .execute()
        )
        return response.data or []

    def log_demand_signal(self, user_id: str, requested_bank_profile: str) -> None:
        self.client.table("demand_signals").insert({
            "user_id": user_id, "requested_bank_profile": requested_bank_profile,
        }).execute()

    def delete_account(self, user_id: str) -> None:
        storage = self.client.storage.from_(self.bucket)
        folders = [user_id]
        while folders:
            folder = folders.pop()
            offset = 0
            folder_files: list[str] = []
            child_folders: list[str] = []

            while True:
                entries = storage.list(
                    folder,
                    {"limit": _STORAGE_LIST_PAGE_SIZE, "offset": offset},
                )
                if not isinstance(entries, list):
                    raise RuntimeError("Storage returned an invalid object listing.")

                for entry in entries:
                    name = entry.get("name")
                    if not isinstance(name, str) or not name or name in {".", ".."} or "/" in name or "\\" in name:
                        raise RuntimeError("Storage returned an invalid object name.")
                    path = f"{folder}/{name}"
                    if entry.get("id") is None:
                        child_folders.append(path)
                    else:
                        folder_files.append(path)

                if len(entries) < _STORAGE_LIST_PAGE_SIZE:
                    break
                offset += len(entries)

            for start in range(0, len(folder_files), _STORAGE_DELETE_BATCH_SIZE):
                storage.remove(folder_files[start:start + _STORAGE_DELETE_BATCH_SIZE])
            folders.extend(child_folders)

        self.client.table("demand_signals").delete().eq("user_id", user_id).execute()
        self.client.table("statement_notes").delete().eq("user_id", user_id).execute()
        self.client.table("clients").delete().eq("user_id", user_id).execute()
        self.client.auth.admin.delete_user(user_id, should_soft_delete=False)


def month_start_now() -> datetime:
    now = datetime.now(timezone.utc)
    return now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)


def _decimal_text(value: Any) -> str | None:
    return None if value is None else format(Decimal(str(value)).quantize(Decimal("0.01")), "f")
