-- Canonical chart-of-accounts reference data for the later classification
-- phase (Main Head / Sub Head), plus an alias table that maps the spelling
-- variants seen in real cash books/GLs to one canonical head.
--
-- Schema only: nothing in the parser or NLP layer reads these tables yet,
-- and nothing here touches transactions.needs_review (always true for
-- heuristic/LLM rows) or statements.confidence.
--
-- Reference data, not per-user data: authenticated users may read it; writes
-- happen only through the backend's service-role key (RLS enabled, no write
-- policies), same least-access pattern as the other tables.
create table public.account_heads (
    id uuid primary key default gen_random_uuid(),
    main_head text not null check (main_head in (
        'Income',
        'Expenses',
        'Accrued and Other Liabilities',
        'Assets',
        'Non-Current Assets',
        'Requires Clarification'
    )),
    sub_head text not null check (sub_head = btrim(sub_head) and sub_head <> ''),
    created_at timestamptz not null default now(),
    unique (main_head, sub_head)
);

-- alias_main / alias_sub are stored already normalized (lower-cased, trimmed,
-- single-spaced); callers must normalize the same way before lookup.
create table public.account_head_aliases (
    id uuid primary key default gen_random_uuid(),
    alias_main text not null,
    alias_sub text not null,
    head_id uuid not null references public.account_heads(id) on delete cascade,
    created_at timestamptz not null default now(),
    unique (alias_main, alias_sub),
    check (alias_main = regexp_replace(lower(btrim(alias_main)), '\s+', ' ', 'g')),
    check (alias_sub = regexp_replace(lower(btrim(alias_sub)), '\s+', ' ', 'g'))
);

create index account_head_aliases_head_id_idx on public.account_head_aliases (head_id);

alter table public.account_heads enable row level security;
alter table public.account_head_aliases enable row level security;

create policy account_heads_read on public.account_heads
    for select to authenticated using (true);
create policy account_head_aliases_read on public.account_head_aliases
    for select to authenticated using (true);
