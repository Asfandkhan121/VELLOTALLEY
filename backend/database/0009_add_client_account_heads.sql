-- A client's own chart of accounts (heads), read from their prior-year trial
-- balance or cash book and CONFIRMED by the user before anything is stored here.
-- Per client, so main heads are free text (real charts have 6, 17 or more); this is
-- separate from the global account_heads reference table.
--
-- Schema only: nothing reads these rows back into parsing or classification, and
-- nothing here touches transactions.needs_review or statements.confidence.
--
-- user_id mirrors the owning client's user_id; the backend sets it from the
-- authenticated user after checking client ownership (RLS is the backup).
create table public.client_account_heads (
    id uuid primary key default gen_random_uuid(),
    client_id uuid not null references public.clients(id) on delete cascade,
    user_id uuid not null references auth.users(id),
    name text not null check (name = btrim(name) and name <> ''),
    section text check (section is null or (section = btrim(section) and section <> '')),
    code text check (code is null or (code = btrim(code) and code <> '')),
    source text not null check (source in ('trial_balance', 'cash_book', 'manual')),
    confirmed_at timestamptz not null default now(),
    created_at timestamptz not null default now()
);

-- one head per name per client, ignoring case and spacing
create unique index client_account_heads_client_name_uniq
    on public.client_account_heads (client_id, lower(regexp_replace(name, '\s+', ' ', 'g')));

create index client_account_heads_client_id_idx on public.client_account_heads (client_id);

alter table public.client_account_heads enable row level security;

create policy client_account_heads_owner_all
    on public.client_account_heads
    for all
    using (auth.uid() = user_id)
    with check (auth.uid() = user_id);
