# Website roadmap

The website presents three distinct product phases. Only Phase 1 is
currently available as an end-to-end user workflow. The Phase 2 and Phase
3 descriptions are the intended experience, not implemented capabilities.

## Phase 1 — Bank statement converter

1. Choose a client.
2. Select a known bank profile or automatic layout detection.
3. Upload a bank-statement PDF.
4. Review extracted transactions, uncertainty, and balance information.
5. Download the structured Excel file.

This phase stays focused on PDF-to-Excel bank statement conversion.

## Phase 2 — Raw bookkeeping data categorization

The future workflow accepts raw cash books and supporting accounting
records. The user can provide a prior-year Trial Balance or financial
statements to inform the organization's cash/accrual basis, existing
heads, opening balances, and recurring transaction treatment. Proposed
general-purpose heads derived from owner-provided accounting data are a
starting point, not a replacement for the organization's own prior-year
heads. If necessary information is missing, the website asks focused
questions before using assumptions.

The review workspace will propose consistent Main Heads and Sub Heads for
recurring transactions, show source evidence, preserve the original
records, and let users correct or approve suggestions. The output is
clean, pivot-ready categorized data—not an automatically approved
accounting result.

Questions should be asked only when source records leave a real gap. The
question bank should cover organization and period, currency, cash versus
accrual basis, prior-year head mapping, source-file coverage, recurring
transaction treatment, and missing payroll/fee/receivable schedules.
Phase 3 questions should cover opening balances, prior-year financials,
missing balances or disclosures, and requested statements/comparatives.
The accountant reviews this question bank before it is used to produce
financial outputs.

## Phase 3 — Trial Balance and financial statements

The future workflow uses reviewed Phase 2 data to prepare a Trial
Balance. It asks for prior-year financials or missing details through
focused questions, surfaces unresolved issues, and lets the user review
the completed statements. Approved outputs are downloadable as Excel and
PDF.

## User experience requirements

- Keep conversion, categorization, and financial-statement preparation
  visibly distinct.
- Reuse answers and source records across phases rather than asking the
  same questions repeatedly.
- Show loading, validation, needs-information, review, failure, retry, and
  export-ready states.
- Preserve accessible keyboard navigation, responsive tables, and clear
  status labels.
- Never advertise Phase 2 or Phase 3 as available until their workflows
  work end to end.
