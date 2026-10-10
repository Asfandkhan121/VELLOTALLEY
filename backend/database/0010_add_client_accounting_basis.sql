-- Per-client accounting basis. The user confirms the value; nothing may
-- infer it from a trial balance, an audited PDF, or a guess.
--
-- 'unset' is the default for every existing and new client. While a client
-- is unset, payroll and income rows stay needs_review. This file does not
-- touch transactions.needs_review or statements.confidence, and it does not
-- set any client to accrual or cash.
--
-- Schema only. Do not apply to the live database without the owner's go-ahead.
alter table public.clients
    add column accounting_basis text not null default 'unset'
        check (accounting_basis in ('accrual', 'cash', 'modified_cash', 'unset'));
