# Private FastAPI-to-Supabase validation

Run these steps only on your own secured machine. Do not paste `SUPABASE_SERVICE_ROLE_KEY` or a newer `sb_secret_...` key into any AI chat, handoff, source file, ZIP, URL, or frontend variable.

## Start the API

Create a private `.env` file from `.env.example`, fill in your Supabase URL and backend-only secret, then keep that file out of Git and ZIP archives. Create the already-documented private `statements` Storage bucket if it is missing.

Install dependencies into an isolated virtual environment, then start the app factory:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
uvicorn app.main:app_factory --factory --reload
```

## Validate with two real test users

Obtain normal Supabase access tokens for User A and User B via your app/Auth flow. They are user tokens, not service secrets.

For User A, create a client row first. Then verify:

1. Upload a supported real PDF using `POST /v1/statements` with `client_id`, `bank_profile`, and multipart `file`.
2. Call `POST /v1/statements/{id}/extract`; confirm returned transaction count and printed final balance.
3. Call `GET /v1/statements/{id}/excel`; open the workbook and check totals and order.
4. User B must receive 404 when trying to extract/download User A's statement.
5. Confirm 401 for missing/invalid tokens, 415 for a non-PDF, 422 for an unsupported profile, and 429 for the fourth current-month conversion on the free tier.

After validation, remove test records and Storage objects using approved maintenance tooling. Do not test with production customer data unless you have explicit authorization.
