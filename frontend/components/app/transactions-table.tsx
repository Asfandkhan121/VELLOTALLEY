import { AlertTriangle } from 'lucide-react'
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table'
import { formatAmount, formatDate } from '@/lib/format'
import { cn } from '@/lib/utils'
import type { Transaction } from '@/lib/types'

function ReviewFlag() {
  return (
    <span className="inline-flex items-center gap-1 rounded-full border border-warning/40 bg-warning/10 px-2 py-0.5 text-xs font-medium text-warning-foreground dark:text-warning">
      <AlertTriangle className="size-3.5" aria-hidden="true" />
      Review
    </span>
  )
}

function Amount({ value, kind }: { value: Transaction['debit']; kind: 'debit' | 'credit' | 'balance' }) {
  if (value === null || value === '' || value === undefined) {
    return <span className="text-muted-foreground/50">—</span>
  }
  return (
    <span className="font-mono tabular-nums">
      {kind === 'debit' ? <span className="mr-0.5 text-muted-foreground">Dr</span> : null}
      {kind === 'credit' ? <span className="mr-0.5 text-muted-foreground">Cr</span> : null}
      {formatAmount(value)}
    </span>
  )
}

export function TransactionsTable({ transactions }: { transactions: Transaction[] }) {
  return (
    <>
      {/* Desktop / tablet table */}
      <div className="hidden overflow-hidden rounded-xl border md:block">
        <Table>
          <TableHeader>
            <TableRow className="bg-muted/40">
              <TableHead className="w-28">Date</TableHead>
              <TableHead>Description</TableHead>
              <TableHead className="text-right">Debit</TableHead>
              <TableHead className="text-right">Credit</TableHead>
              <TableHead className="text-right">Balance</TableHead>
              <TableHead className="text-right">Review</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {transactions.map((tx, index) => (
              <TableRow
                key={index}
                className={cn(tx.needs_review && 'bg-warning/5 hover:bg-warning/10')}
              >
                <TableCell className="whitespace-nowrap text-muted-foreground">
                  {tx.date ? formatDate(tx.date) : <span className="text-muted-foreground/50">—</span>}
                </TableCell>
                <TableCell className="max-w-[24rem] font-medium">
                  <span className="block truncate" title={tx.description ?? undefined}>
                    {tx.description || <span className="text-muted-foreground/50">—</span>}
                  </span>
                </TableCell>
                <TableCell className="text-right">
                  <Amount value={tx.debit} kind="debit" />
                </TableCell>
                <TableCell className="text-right">
                  <Amount value={tx.credit} kind="credit" />
                </TableCell>
                <TableCell className="text-right">
                  <Amount value={tx.balance} kind="balance" />
                </TableCell>
                <TableCell className="text-right">{tx.needs_review ? <ReviewFlag /> : null}</TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </div>

      {/* Mobile cards */}
      <ul className="flex flex-col gap-3 md:hidden">
        {transactions.map((tx, index) => (
          <li
            key={index}
            className={cn('rounded-xl border p-4', tx.needs_review && 'border-warning/40 bg-warning/5')}
          >
            <div className="flex items-start justify-between gap-3">
              <div className="min-w-0">
                <p className="font-medium">
                  {tx.description || <span className="text-muted-foreground/50">—</span>}
                </p>
                <p className="mt-0.5 text-xs text-muted-foreground">
                  {tx.date ? formatDate(tx.date) : 'No date'}
                </p>
              </div>
              {tx.needs_review ? <ReviewFlag /> : null}
            </div>
            <dl className="mt-3 grid grid-cols-3 gap-2 border-t pt-3 text-sm">
              <div className="flex flex-col gap-0.5">
                <dt className="text-xs text-muted-foreground">Debit</dt>
                <dd>
                  <Amount value={tx.debit} kind="debit" />
                </dd>
              </div>
              <div className="flex flex-col gap-0.5">
                <dt className="text-xs text-muted-foreground">Credit</dt>
                <dd>
                  <Amount value={tx.credit} kind="credit" />
                </dd>
              </div>
              <div className="flex flex-col gap-0.5">
                <dt className="text-xs text-muted-foreground">Balance</dt>
                <dd>
                  <Amount value={tx.balance} kind="balance" />
                </dd>
              </div>
            </dl>
          </li>
        ))}
      </ul>
    </>
  )
}
