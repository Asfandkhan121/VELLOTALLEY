-- Captures real demand: every time someone requests a bank_profile that
-- doesn't exist yet, that request is currently just thrown away as a 422
-- with no record. This logs it instead, so "which banks should we build
-- next" is answered from real usage data, not guesswork.
--
-- Deliberately locked down (RLS enabled, zero policies): this is internal
-- analytics, written and read only by the backend's service-role key, which
-- bypasses RLS entirely -- no authenticated user reads or writes it via
-- their own JWT. Same reasoning as every other table here: least access by
-- default, backend enforces the real logic.
create table public.demand_signals (
    id uuid primary key default gen_random_uuid(),
    user_id uuid references auth.users(id),
    requested_bank_profile text not null,
    created_at timestamptz not null default now()
);

create index demand_signals_requested_bank_profile_idx on public.demand_signals (requested_bank_profile);

alter table public.demand_signals enable row level security;
