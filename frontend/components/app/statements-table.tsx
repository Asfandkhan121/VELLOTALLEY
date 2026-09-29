import Link from 'next/link'
import { ChevronRight } from 'lucide-react'
import { Button } from '@/components/ui/button'
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table'
import { ConfidenceBadge, StatusBadge } from '@/components/shared/status-badges'
import { DownloadExcelButton } from '@/components/shared/statement-actions'
import { bankLabel, displayStatus, formatDate } from '@/lib/format'
import type { Statement } from '@/lib/types'

function RowActions({ statement }: { statement: Statement }) {
  const status = displayStatus(statement)
  const downloadable = status === 'completed' || status === 'needs_review'
  return (
    <div className="flex items-center justify-end gap-1">
      {downloadable ? (
        <DownloadExcelButton
          statementId={statement.id}
          filename={statement.original_filename}
          label="Excel"
          variant="ghost"
          size="sm"
        />
      ) : null}
      <Button
        variant="ghost"
        size="icon-sm"
        aria-label={`Open ${statement.original_filename}`}
        render={<Link href={`/statements/${statement.id}`} />}
      >
        <ChevronRight aria-hidden="true" />
      </Button>
    </div>
  )
}

export function StatementsTable({
  statements,
  clientMap,
}: {
  statements: Statement[]
  clientMap: Map<string, string>
}) {
  return (
    <>
      {/* Desktop / tablet table */}
      <div className="hidden overflow-hidden rounded-xl border md:block">
        <Table>
          <TableHeader>
            <TableRow className="bg-muted/40">
              <TableHead>Statement</TableHead>
              <TableHead>Client</TableHead>
              <TableHead className="hidden lg:table-cell">Bank</TableHead>
              <TableHead className="hidden lg:table-cell">Uploaded</TableHead>
              <TableHead>Status</TableHead>
              <TableHead className="hidden xl:table-cell">Confidence</TableHead>
              <TableHead className="text-right">Actions</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {statements.map((statement) => (
              <TableRow key={statement.id} className="group">
                <TableCell className="max-w-[16rem] font-medium">
                  <Link
                    href={`/statements/${statement.id}`}
                    className="block truncate underline-offset-4 outline-none group-hover:underline focus-visible:underline"
                    title={statement.original_filename}
                  >
                    {statement.original_filename}
                  </Link>
                </TableCell>
                <TableCell className="max-w-[12rem] truncate text-muted-foreground">
                  {clientMap.get(statement.client_id) ?? '—'}
                </TableCell>
                <TableCell className="hidden text-muted-foreground lg:table-cell">
                  {bankLabel(statement.bank_profile)}
                </TableCell>
                <TableCell className="hidden whitespace-nowrap text-muted-foreground lg:table-cell">
                  {formatDate(statement.uploaded_at)}
                </TableCell>
                <TableCell>
                  <StatusBadge status={displayStatus(statement)} />
                </TableCell>
                <TableCell className="hidden xl:table-cell">
                  <ConfidenceBadge confidence={statement.confidence} />
                </TableCell>
                <TableCell className="text-right">
                  <RowActions statement={statement} />
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </div>

      {/* Mobile cards */}
      <ul className="flex flex-col gap-3 md:hidden">
        {statements.map((statement) => (
          <li key={statement.id} className="rounded-xl border p-4">
            <div className="flex items-start justify-between gap-3">
              <Link
                href={`/statements/${statement.id}`}
                className="min-w-0 flex-1 font-medium underline-offset-4 outline-none hover:underline focus-visible:underline"
              >
                <span className="block truncate" title={statement.original_filename}>
                  {statement.original_filename}
                </span>
                <span className="mt-0.5 block truncate text-sm text-muted-foreground">
                  {clientMap.get(statement.client_id) ?? '—'} · {bankLabel(statement.bank_profile)}
                </span>
              </Link>
              <StatusBadge status={displayStatus(statement)} />
            </div>
            <div className="mt-3 flex items-center justify-between gap-3">
              <span className="text-xs text-muted-foreground">{formatDate(statement.uploaded_at)}</span>
              <ConfidenceBadge confidence={statement.confidence} />
            </div>
            <div className="mt-3 border-t pt-3">
              <RowActions statement={statement} />
            </div>
          </li>
        ))}
      </ul>
    </>
  )
}
