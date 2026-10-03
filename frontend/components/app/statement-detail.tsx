'use client'

import Link from 'next/link'
import {
  AlertTriangle,
  ArrowLeft,
  CalendarClock,
  FileText,
  Layers,
  Loader2,
} from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Card, CardContent } from '@/components/ui/card'
import { Skeleton } from '@/components/ui/skeleton'
import { StatementNotes } from '@/components/app/statement-notes'
import { TransactionsTable } from '@/components/app/transactions-table'
import { ErrorState, PageHeader } from '@/components/shared/states'
import {
  ConfidenceBadge,
  MethodBadge,
  StatusBadge,
} from '@/components/shared/status-badges'
import { DownloadExcelButton, RetryExtractionButton } from '@/components/shared/statement-actions'
import { bankLabel, displayStatus, formatDate } from '@/lib/format'
import { useClientMap, useStatement, useTransactions } from '@/lib/hooks'

function BackLink() {
  return (
    <Button nativeButton={false} variant="ghost" size="sm" className="-ml-2 w-fit" render={<Link href="/statements" />}>
      <ArrowLeft aria-hidden="true" />
      Statements
    </Button>
  )
}

function DetailItem({
  icon: Icon,
  label,
  children,
}: {
  icon: typeof FileText
  label: string
  children: React.ReactNode
}) {
  return (
    <div className="flex flex-col gap-1">
      <span className="flex items-center gap-1.5 text-xs font-medium text-muted-foreground">
        <Icon className="size-3.5" aria-hidden="true" />
        {label}
      </span>
      <div className="text-sm">{children}</div>
    </div>
  )
}

export function StatementDetail({ id }: { id: string }) {
  const { data: statement, error, isLoading, mutate } = useStatement(id)
  const clientMap = useClientMap()

  const status = statement ? displayStatus(statement) : null
  const transactionsEnabled = statement?.status === 'completed'
  const transactions = useTransactions(id, Boolean(transactionsEnabled))

  if (error) {
    return (
      <>
        <BackLink />
        <ErrorState error={error} title="Could not load statement" onRetry={() => mutate()} />
      </>
    )
  }

  if (isLoading || !statement) {
    return (
      <>
        <BackLink />
        <Skeleton className="h-9 w-72" />
        <Skeleton className="h-32 w-full rounded-xl" />
        <Skeleton className="h-64 w-full rounded-xl" />
      </>
    )
  }

  const clientName = clientMap.get(statement.client_id) ?? 'Unknown client'
  const downloadable = status === 'completed' || status === 'needs_review'
  const txList = transactions.data ?? []
  const reviewCount = txList.filter((tx) => tx.needs_review).length

  return (
    <>
      <BackLink />

      <PageHeader
        title={statement.original_filename}
        description={`${clientName} · ${bankLabel(statement.bank_profile)} · Uploaded ${formatDate(statement.uploaded_at)}`}
        actions={
          <>
            {downloadable ? (
              <DownloadExcelButton
                statementId={statement.id}
                filename={statement.original_filename}
                label="Download Excel"
              />
            ) : null}
            {statement.status === 'failed' ? (
              <RetryExtractionButton statementId={statement.id} onSettled={() => mutate()} />
            ) : null}
          </>
        }
      />

      {/* Summary */}
      <Card>
        <CardContent className="flex flex-wrap items-start gap-x-8 gap-y-4">
          <DetailItem icon={FileText} label="Status">
            {status ? <StatusBadge status={status} /> : '—'}
          </DetailItem>
          <DetailItem icon={Layers} label="Method">
            <MethodBadge method={statement.extraction_method} />
          </DetailItem>
          <DetailItem icon={AlertTriangle} label="Confidence">
            <ConfidenceBadge confidence={statement.confidence} />
          </DetailItem>
          {statement.layout_detected ? (
            <DetailItem icon={Layers} label="Layout detected">
              <span className="text-muted-foreground">{statement.layout_detected}</span>
            </DetailItem>
          ) : null}
        </CardContent>
      </Card>

      {statement.date_format_ambiguous ? (
        <div
          role="note"
          className="flex items-start gap-2.5 rounded-lg border border-warning/40 bg-warning/10 px-4 py-3 text-sm text-warning-foreground dark:text-warning"
        >
          <CalendarClock className="mt-0.5 size-4 shrink-0" aria-hidden="true" />
          <p className="text-pretty">
            The date format in this statement was ambiguous (for example, day/month vs. month/day).
            Double-check transaction dates before relying on the export.
          </p>
        </div>
      ) : null}

      {/* State-specific body */}
      {statement.status === 'processing' ? (
        <Card>
          <CardContent className="flex flex-col items-center justify-center gap-3 py-12 text-center">
            <Loader2 className="size-6 animate-spin text-info" aria-hidden="true" />
            <div className="flex max-w-sm flex-col gap-1">
              <h3 className="font-medium">Extraction in progress</h3>
              <p className="text-sm text-muted-foreground text-pretty">
                We&apos;re reading the statement and extracting transactions. This page updates
                automatically when it&apos;s ready.
              </p>
            </div>
          </CardContent>
        </Card>
      ) : statement.status === 'failed' ? (
        <Card>
          <CardContent className="flex flex-col items-center justify-center gap-3 py-12 text-center">
            <div className="flex size-11 items-center justify-center rounded-full bg-destructive/10 text-destructive">
              <AlertTriangle className="size-5" aria-hidden="true" />
            </div>
            <div className="flex max-w-md flex-col gap-1">
              <h3 className="font-medium">Extraction failed</h3>
              <p className="text-sm text-muted-foreground text-pretty">
                We couldn&apos;t extract transactions from this statement. This can happen with
                scanned or password-protected PDFs. Try running the extraction again.
              </p>
            </div>
            <RetryExtractionButton
              statementId={statement.id}
              variant="outline"
              size="sm"
              onSettled={() => mutate()}
            />
          </CardContent>
        </Card>
      ) : (
        <section aria-label="Transactions" className="flex flex-col gap-4">
          <div className="flex flex-wrap items-center justify-between gap-2">
            <h2 className="text-lg font-semibold tracking-tight">Transactions</h2>
            {transactions.data ? (
              <p className="text-sm text-muted-foreground">
                {txList.length} {txList.length === 1 ? 'transaction' : 'transactions'}
                {reviewCount > 0 ? (
                  <>
                    {' · '}
                    <span className="font-medium text-warning-foreground dark:text-warning">
                      {reviewCount} need review
                    </span>
                  </>
                ) : null}
              </p>
            ) : null}
          </div>
          <p className="text-xs text-muted-foreground">
            NLP hints analyze transaction wording only. They do not verify amounts or balances and
            never change a transaction&apos;s review flag.
          </p>

          {transactions.error ? (
            <ErrorState
              error={transactions.error}
              title="Could not load transactions"
              onRetry={() => transactions.mutate()}
            />
          ) : transactions.isLoading ? (
            <div className="flex flex-col gap-3">
              <Skeleton className="h-12 w-full rounded-xl" />
              <Skeleton className="h-12 w-full rounded-xl" />
              <Skeleton className="h-12 w-full rounded-xl" />
            </div>
          ) : txList.length === 0 ? (
            <div className="rounded-xl border border-dashed px-6 py-10 text-center text-sm text-muted-foreground">
              No transactions were extracted from this statement.
            </div>
          ) : (
            <TransactionsTable transactions={txList} />
          )}
        </section>
      )}

      <StatementNotes statementId={statement.id} />
    </>
  )
}
