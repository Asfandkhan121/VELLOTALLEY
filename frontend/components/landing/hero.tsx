import Link from 'next/link'
import { ArrowRight, FileText, FileSpreadsheet } from 'lucide-react'
import { Button } from '@/components/ui/button'

const PREVIEW_ROWS = [
  { date: '01 Mar 2026', description: 'Opening balance', debit: '', credit: '', balance: '245,300.00' },
  { date: '03 Mar 2026', description: 'IBFT transfer — Rahim Traders', debit: '', credit: '58,000.00', balance: '303,300.00' },
  { date: '05 Mar 2026', description: 'K-Electric bill payment', debit: '12,480.50', credit: '', balance: '290,819.50' },
  { date: '09 Mar 2026', description: 'Cheque 004517 cleared', debit: '75,000.00', credit: '', balance: '215,819.50', review: true },
  { date: '12 Mar 2026', description: 'POS purchase — Metro Cash', debit: '8,960.00', credit: '', balance: '206,859.50' },
]

export function Hero({ signedIn }: { signedIn: boolean }) {
  return (
    <section className="relative overflow-hidden border-b">
      <div className="mx-auto flex max-w-6xl flex-col gap-12 px-4 py-16 sm:px-6 md:py-24 lg:flex-row lg:items-center">
        <div className="flex flex-1 flex-col gap-6">
          <p className="inline-flex w-fit items-center gap-2 rounded-full border bg-card px-3 py-1 text-xs font-medium text-muted-foreground">
            <span className="size-1.5 rounded-full bg-primary" aria-hidden="true" />
            Built for accountants and bookkeepers
          </p>
          <h1 className="text-4xl font-semibold tracking-tight text-balance sm:text-5xl">
            Bank statement PDFs to clean Excel, in minutes.
          </h1>
          <p className="max-w-xl text-lg leading-relaxed text-muted-foreground text-pretty">
            Upload a statement, organise it under the right client, and download a structured
            spreadsheet with dates, descriptions, debits, credits and balances — ready for
            reconciliation.
          </p>
          <div className="flex flex-col gap-3 sm:flex-row">
            <Button render={<Link href={signedIn ? '/statements/new' : '/signup'} />} size="lg">
              {signedIn ? 'Convert a statement' : 'Start converting free'}
              <ArrowRight aria-hidden="true" />
            </Button>
            <Button render={<Link href={signedIn ? '/dashboard' : '/login'} />} size="lg" variant="outline">
              {signedIn ? 'Open dashboard' : 'Log in'}
            </Button>
          </div>
          <p className="text-sm text-muted-foreground">
            3 free conversions every month. No card required.
          </p>
        </div>

        <div className="flex-1" aria-hidden="true">
          <div className="rounded-2xl border bg-card p-4 shadow-sm">
            <div className="flex items-center justify-between gap-3 border-b pb-3">
              <div className="flex items-center gap-2 text-sm">
                <FileText className="size-4 text-muted-foreground" />
                <span className="font-medium">march-2026-statement.pdf</span>
              </div>
              <span className="inline-flex items-center gap-1.5 rounded-full border border-success/30 bg-success/10 px-2 py-0.5 text-xs font-medium text-success">
                <FileSpreadsheet className="size-3.5" />
                Excel ready
              </span>
            </div>
            <div className="overflow-hidden pt-3">
              <table className="w-full text-left text-xs">
                <thead className="text-muted-foreground">
                  <tr>
                    <th className="py-2 pr-3 font-medium">Date</th>
                    <th className="py-2 pr-3 font-medium">Description</th>
                    <th className="hidden py-2 pr-3 text-right font-medium sm:table-cell">Debit</th>
                    <th className="hidden py-2 pr-3 text-right font-medium sm:table-cell">Credit</th>
                    <th className="py-2 text-right font-medium">Balance</th>
                  </tr>
                </thead>
                <tbody className="font-mono tabular-nums">
                  {PREVIEW_ROWS.map((row) => (
                    <tr key={row.date + row.description} className={row.review ? 'bg-warning/10' : 'border-t'}>
                      <td className="py-2 pr-3 whitespace-nowrap">{row.date}</td>
                      <td className="max-w-40 truncate py-2 pr-3 font-sans">{row.description}</td>
                      <td className="hidden py-2 pr-3 text-right sm:table-cell">{row.debit}</td>
                      <td className="hidden py-2 pr-3 text-right text-success sm:table-cell">{row.credit}</td>
                      <td className="py-2 text-right">{row.balance}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            <div className="mt-3 flex items-center justify-between rounded-lg bg-muted px-3 py-2 text-xs text-muted-foreground">
              <span>1 row flagged for review</span>
              <span className="font-mono tabular-nums">Confidence 94%</span>
            </div>
          </div>
        </div>
      </div>
    </section>
  )
}
