-- These nullable columns are reserved for the later transaction
-- classification/reconciliation phase.  Keeping them in a migration makes
-- a new deployment reproduce the live schema rather than depending on
-- untracked manual SQL.
ALTER TABLE public.transactions
    ADD COLUMN IF NOT EXISTS category text,
    ADD COLUMN IF NOT EXISTS matched_status text;

COMMENT ON COLUMN public.transactions.category IS
    'Optional accounting category assigned during transaction classification.';
COMMENT ON COLUMN public.transactions.matched_status IS
    'Optional reconciliation/matching state assigned after extraction.';
