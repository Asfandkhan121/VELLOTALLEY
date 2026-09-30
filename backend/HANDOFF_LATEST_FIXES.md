# Complete Converter handoff

This is the original `v9_pkg` application, merged with the later Converter
update and review fixes. It intentionally excludes the original `.env`, token
files, virtual environment, Python bytecode, and generated spreadsheets.

## Merged update

- `app/main.py`, `app/config.py`, and `app/repository.py` contain the newer
  profile -> heuristic -> LLM extraction orchestration.
- `llm_parser.py` is included as the last-resort Anthropic PDF parser.
- `heuristic_parser.py` includes the signed-amount column fix: it detects
  right-aligned monetary columns by `x1`, which prevents negative and
  positive values in one amount column from being split into separate columns.
- `requirements.txt` explicitly pins `httpx` and `python-dotenv` in addition
  to the original package's dependencies.
- Database migrations `0006` and `0007` are placed beside the original
  migrations `0003`-`0005`, matching the original project's convention.

## Before deployment

1. Copy `.env.example` to `.env` and provide server-only credentials outside
   source control.
2. Apply migrations in sequence through the project's normal Supabase
   migration workflow.
3. Run the test suite and an authenticated upload/extract smoke test.

The live Supabase schema has not been queried from this package yet; the
Codex Supabase MCP connection is authenticated read-only but must be loaded
in a fresh task/session to inspect it.
