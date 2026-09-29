-- Required for stable statement order on preview and Excel re-downloads.
-- Dates are not sufficient: several bank statements contain multiple entries
-- on the same date, and UUID primary keys do not preserve printed order.
alter table public.transactions
    add column transaction_sequence integer;

update public.transactions
set transaction_sequence = ordered.sequence
from (
    select id, row_number() over (partition by statement_id order by date, id) as sequence
    from public.transactions
) as ordered
where public.transactions.id = ordered.id;

alter table public.transactions
    alter column transaction_sequence set not null;

create unique index transactions_statement_sequence_idx
    on public.transactions (statement_id, transaction_sequence);
