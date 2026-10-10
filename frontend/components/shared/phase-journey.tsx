import Link from 'next/link'
import { Button } from '@/components/ui/button'

const PHASES = [
  {
    number: 'Phase 1',
    title: 'Convert bank statements',
    status: 'Available now',
    available: true,
    description:
      'Turn a bank-statement PDF into a clean Excel file, then review the extracted dates, descriptions, debits, credits and balances.',
  },
  {
    number: 'Phase 2',
    title: 'Categorize raw bookkeeping data',
    status: 'Planned',
    available: false,
    description:
      'Read raw cash books and supporting records, then categorize recurring transactions under consistent Main Heads and Sub Heads. Start from the general-purpose heads prepared from owner-provided data, refine them using prior-year records, and ask questions when needed to produce reviewed, pivot-ready data.',
  },
  {
    number: 'Phase 3',
    title: 'Prepare the Trial Balance and financial statements',
    status: 'Planned',
    available: false,
    description:
      'Build a Trial Balance from reviewed categorized data, gather prior-year financials or answers to outstanding questions, and prepare the approved financial statements for Excel and PDF.',
  },
] as const

export function PhaseJourney({ signedIn = false }: { signedIn?: boolean }) {
  return (
    <div className="flex flex-col gap-7">
      <div className="flex flex-col gap-2">
        <h2 className="text-2xl font-semibold tracking-tight text-balance sm:text-3xl">
          From source records to complete financials
        </h2>
        <p className="max-w-2xl text-sm leading-relaxed text-muted-foreground text-pretty">
          The work happens in three distinct phases. The bank-statement converter is the only
          phase available today; the later accounting workflows are planned, not yet usable.
        </p>
      </div>

      <ol aria-label="Vellotalley product phases" className="divide-y rounded-xl border bg-card">
        {PHASES.map((phase) => (
          <li key={phase.number} className="flex flex-col gap-4 p-5 sm:flex-row sm:items-start sm:justify-between sm:gap-8 sm:p-6">
            <div className="flex min-w-0 gap-4">
              <span
                aria-hidden="true"
                className={
                  phase.available
                    ? 'mt-1 flex size-8 shrink-0 items-center justify-center rounded-full bg-primary text-xs font-semibold text-primary-foreground'
                    : 'mt-1 flex size-8 shrink-0 items-center justify-center rounded-full border bg-muted text-xs font-semibold text-muted-foreground'
                }
              >
                {phase.number.slice(-1)}
              </span>
              <div className="flex min-w-0 flex-col gap-2">
                <div className="flex flex-wrap items-center gap-2">
                  <span className="text-xs font-medium text-muted-foreground">{phase.number}</span>
                  <span
                    className={
                      phase.available
                        ? 'rounded-full bg-success/10 px-2 py-0.5 text-xs font-medium text-success'
                        : 'rounded-full bg-muted px-2 py-0.5 text-xs font-medium text-muted-foreground'
                    }
                  >
                    {phase.status}
                  </span>
                </div>
                <h3 className="font-medium">{phase.title}</h3>
                <p className="max-w-3xl text-sm leading-relaxed text-muted-foreground">
                  {phase.description}
                </p>
              </div>
            </div>
            {phase.available ? (
              <Button
                className="shrink-0 sm:mt-1"
                nativeButton={false}
                render={<Link href={signedIn ? '/statements/new' : '/signup'} />}
                variant="outline"
              >
                {signedIn ? 'Convert a statement' : 'Start converting free'}
              </Button>
            ) : null}
          </li>
        ))}
      </ol>
    </div>
  )
}
