from __future__ import annotations

from dataclasses import dataclass
import os

from dotenv import load_dotenv

load_dotenv()  # so the app loads .env on its own -- previously this only
                # worked because uvicorn was started with --env-file .env;
                # anyone starting it a different way (a process manager, a
                # different launch command) hit the same "must be configured
                # on the server" error for the same avoidable reason.


@dataclass(frozen=True)
class Settings:
    supabase_url: str
    supabase_service_role_key: str
    statement_bucket: str = "statements"
    free_monthly_limit: int = 3
    anthropic_api_key: str | None = None

    @classmethod
    def from_environment(cls) -> "Settings":
        url = os.environ.get("SUPABASE_URL", "")
        key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY", "")
        if not url or not key:
            raise RuntimeError("SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY must be configured on the server.")
        return cls(
            supabase_url=url,
            supabase_service_role_key=key,
            statement_bucket=os.environ.get("STATEMENT_BUCKET", "statements"),
            free_monthly_limit=int(os.environ.get("FREE_MONTHLY_LIMIT", "3")),
            # Deliberately optional, no hard failure if unset -- the LLM
            # fallback is a nice-to-have, not something that should crash
            # the whole app at startup if it's not configured yet. Missing
            # it only matters at the moment bank_profile="auto" actually
            # needs to escalate past the heuristic path, where the
            # resulting API auth failure surfaces as a normal clean 422 to
            # that one request, not a startup crash.
            anthropic_api_key=os.environ.get("ANTHROPIC_API_KEY") or None,
        )
