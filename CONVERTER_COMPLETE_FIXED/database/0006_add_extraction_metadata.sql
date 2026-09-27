-- Persist which extraction tier produced a statement and how well its
-- balance chain validated.  IF NOT EXISTS makes this safe for environments
-- where the migration was applied manually before it was checked in.
ALTER TABLE public.statements
    ADD COLUMN IF NOT EXISTS extraction_method text,
    ADD COLUMN IF NOT EXISTS confidence numeric;

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM pg_constraint
        WHERE conname = 'statements_extraction_method_check'
          AND conrelid = 'public.statements'::regclass
    ) THEN
        ALTER TABLE public.statements
            ADD CONSTRAINT statements_extraction_method_check
            CHECK (extraction_method IS NULL OR extraction_method IN ('profile', 'heuristic', 'llm'));
    END IF;

    IF NOT EXISTS (
        SELECT 1
        FROM pg_constraint
        WHERE conname = 'statements_confidence_check'
          AND conrelid = 'public.statements'::regclass
    ) THEN
        ALTER TABLE public.statements
            ADD CONSTRAINT statements_confidence_check
            CHECK (confidence IS NULL OR confidence BETWEEN 0 AND 1);
    END IF;
END $$;

COMMENT ON COLUMN public.statements.extraction_method IS
    'Parser tier that completed extraction: profile, heuristic, or llm.';
COMMENT ON COLUMN public.statements.confidence IS
    'Balance-chain validation ratio for heuristic and LLM extraction, from 0 to 1.';
