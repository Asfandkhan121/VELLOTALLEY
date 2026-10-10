'use client'

import Link from 'next/link'
import {
  AlertTriangle,
  FileText,
  Loader2,
  Plus,
  Users,
  type LucideIcon,
} from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Card, CardContent } from '@/components/ui/card'
import { Skeleton } from '@/components/ui/skeleton'
import { StatementsTable } from '@/components/app/statements-table'
import { PhaseJourney } from '@/components/shared/phase-journey'
import { EmptyState, ErrorState, PageHeader } from '@/components/shared/states'
import { useClients, useClientMap, useStatements } from '@/lib/hooks'
import { displayStatus } from '@/lib/format'
import type { Statement } from '@/lib/types'

function StatCard({
  icon: Icon,
  label,
  value,
  loading,
  accent,
}: {
  icon: LucideIcon
  label: string
  value: number
  loading: boolean
  accent?: 'warning' | 'info'
}) {
  return (
    <Card>
      <CardContent className="flex items-center gap-3">
        <span
          className={
            accent === 'warning'
              ? 'flex size-9 shrink-0 items-center justify-center rounded-lg bg-warning/10 text-warning-foreground dark:text-warning'
              : accent === 'info'
                ? 'flex size-9 shrink-0 items-center justify-center rounded-lg bg-info/10 text-info'
                : 'flex size-9 shrink-0 items-center justify-center rounded-lg bg-accent text-accent-foreground'
          }
        >
          <Icon className="size-4.5" aria-hidden="true" />
        </span>
        <div className="flex flex-col">
          <span className="text-xs font-medium text-muted-foreground">{label}</span>
          {loading ? (
            <Skeleton className="mt-1 h-7 w-10" />
          ) : (
            <span className="text-2xl font-semibold tabular-nums">{value}</span>
          )}
        </div>
      </CardContent>
    </Card>
  )
}

function sortByUploadedDesc(statements: Statement[]): Statement[] {
  return [...statements].sort(
    (a, b) => new Date(b.uploaded_at).getTime() - new Date(a.uploaded_at).getTime(),
  )
}

export default function DashboardPage() {
  const clients = useClients()
  const statements = useStatements()
  const clientMap = useClientMap()

  const clientCount = clients.data?.length ?? 0
  const statementList = statements.data ?? []
  const statementCount = statementList.length
  const processingCount = statementList.filter((s) => s.status === 'processing').length
  const reviewCount = statementList.filter((s) => displayStatus(s) === 'needs_review').length

  const loading = clients.isLoading || statements.isLoading
  const recent = sortByUploadedDesc(statementList).slice(0, 6)

  return (
    <>
      <PageHeader
        title="Dashboard"
        description="Convert bank-statement PDFs to Excel today, then follow the planned path toward categorized bookkeeping data and financial statements."
        actions={
          <Button nativeButton={false} render={<Link href="/statements/new" />}>
            <Plus aria-hidden="true" />
            New conversion
          </Button>
        }
      />

      <PhaseJourney signedIn />

      <section aria-label="Overview" className="grid grid-cols-2 gap-4 lg:grid-cols-4">
        <StatCard icon={Users} label="Clients" value={clientCount} loading={loading} />
        <StatCard icon={FileText} label="Statements" value={statementCount} loading={loading} />
        <StatCard
          icon={Loader2}
          label="Processing"
          value={processingCount}
          loading={loading}
          accent="info"
        />
        <StatCard
          icon={AlertTriangle}
          label="Need review"
          value={reviewCount}
          loading={loading}
          accent="warning"
        />
      </section>

      <section aria-label="Recent statements" className="flex flex-col gap-4">
        <div className="flex items-center justify-between gap-3">
          <h2 className="text-lg font-semibold tracking-tight">Recent statements</h2>
          {statementCount > 0 ? (
            <Button nativeButton={false} variant="ghost" size="sm" render={<Link href="/statements" />}>
              View all
            </Button>
          ) : null}
        </div>

        {statements.error ? (
          <ErrorState error={statements.error} onRetry={() => statements.mutate()} />
        ) : loading ? (
          <div className="flex flex-col gap-3">
            <Skeleton className="h-12 w-full rounded-xl" />
            <Skeleton className="h-12 w-full rounded-xl" />
            <Skeleton className="h-12 w-full rounded-xl" />
          </div>
        ) : statementCount === 0 ? (
          <EmptyState
            icon={FileText}
            title="No statements yet"
            description="Upload a bank statement PDF to run your first conversion and review the extracted transactions."
            action={
              <Button nativeButton={false} render={<Link href="/statements/new" />}>
                <Plus aria-hidden="true" />
                New conversion
              </Button>
            }
          />
        ) : (
          <StatementsTable statements={recent} clientMap={clientMap} />
        )}
      </section>
    </>
  )
}
