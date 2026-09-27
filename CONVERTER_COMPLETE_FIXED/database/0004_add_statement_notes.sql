-- Lets a user attach a free-text note to a statement -- a correction, a
-- reminder about that bank's quirks ("this account's dates are DD/MM"), or
-- an instruction for the next time this client's statements are converted.
-- Deliberately does NOT feed back into parsing automatically: notes are
-- data for a human (or a future, explicitly-scoped review step) to read and
-- act on, not something the parser reads and self-modifies from. See
-- HANDOFF_v10.md for why that boundary is intentional, not a placeholder.
create table public.statement_notes (
    id uuid primary key default gen_random_uuid(),
    statement_id uuid not null references public.statements(id) on delete cascade,
    user_id uuid not null references auth.users(id),
    note text not null check (char_length(note) between 1 and 2000),
    created_at timestamptz not null default now()
);

create index statement_notes_statement_id_idx on public.statement_notes (statement_id);

alter table public.statement_notes enable row level security;

create policy statement_notes_owner_all
    on public.statement_notes
    for all
    using (auth.uid() = user_id)
    with check (auth.uid() = user_id);
