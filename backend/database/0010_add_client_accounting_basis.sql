-- Per-client accounting basis. NULL = unset (the default): payroll/income rows then stay
-- needs_review and nothing is guessed. A value is only ever written after the user
-- confirms it; the app may recommend a basis but never sets one itself.
-- Schema only: nothing reads this column into parsing or classification yet, and it does
-- not touch transactions.needs_review or statements.confidence.
alter table public.clients
    add column accounting_basis text
        check (accounting_basis is null or accounting_basis in ('accrual', 'cash', 'modified_cash')),
    add column basis_confirmed_at timestamptz,
    add constraint clients_basis_confirmed_together
        check ((accounting_basis is null) = (basis_confirmed_at is null));
