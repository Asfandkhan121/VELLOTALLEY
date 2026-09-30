'use client'

import { Suspense } from 'react'
import Link from 'next/link'
import { useSearchParams } from 'next/navigation'
import { FileText, Plus, X } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Skeleton } from '@/components/ui/skeleton'
import { StatementsTable } from '@/components/app/statements-table'
import { EmptyState, ErrorState, PageHeader } from '@/components/shared/states'
import { useClientMap, useClients, useStatements } from '@/lib/hooks'

export default function StatementsPage() {
  return (
    <Suspense
      fallback={
        <div className="flex flex-col gap-3">
          <Skeleton className="h-12 w-full rounded-xl" />
          <Skeleton className="h-12 w-full rounded-xl" />
        </div>
      }
    >
      <StatementsContent />
    </Suspense>
  )
}

function StatementsContent() {
  const { data, error, isLoading, mutate } = useStatements()
  const clientMap = useClientMap()
  const clients = useClients()
  const searchParams = useSearchParams()

  const clientFilter = searchParams.get('client')
  const filterName = clientFilter ? clients.data?.find((c) => c.id === clientFilter)?.name : null

  const all = data ?? []
  const statements = clientFilter ? all.filter((s) => s.client_id === clientFilter) : all

  return (
    <>
      <PageHeader
        title="Statements"
        description="All uploaded bank statements and their conversion status."
        actions={
          <Button render={<Link href="/statements/new" />}>
            <Plus aria-hidden="true" />
            New conversion
          </Button>
        }
      />

      {clientFilter && filterName ? (
        <div className="flex items-center gap-2 text-sm">
          <span className="text-muted-foreground">Filtered by client:</span>
          <span className="inline-flex items-center gap-1.5 rounded-full border bg-muted/60 px-2 py-0.5 font-medium">
            {filterName}
            <Button
              variant="ghost"
              size="icon-xs"
              aria-label="Clear client filter"
              render={<Link href="/statements" />}
            >
              <X aria-hidden="true" />
            </Button>
          </span>
        </div>
      ) : null}

      {error ? (
        <ErrorState error={error} title="Could not load statements" onRetry={() => mutate()} />
      ) : isLoading ? (
        <div className="flex flex-col gap-3">
          <Skeleton className="h-12 w-full rounded-xl" />
          <Skeleton className="h-12 w-full rounded-xl" />
          <Skeleton className="h-12 w-full rounded-xl" />
          <Skeleton className="h-12 w-full rounded-xl" />
        </div>
      ) : statements.length === 0 ? (
        <EmptyState
          icon={FileText}
          title={clientFilter ? 'No statements for this client' : 'No statements yet'}
          description={
            clientFilter
              ? 'This client has no statements yet. Start a conversion to add one.'
              : 'Convert a bank statement PDF to see it listed here with its extraction status and confidence.'
          }
          action={
            <Button render={<Link href="/statements/new" />}>
              <Plus aria-hidden="true" />
              Convert a statement
            </Button>
          }
        />
      ) : (
        <StatementsTable statements={statements} clientMap={clientMap} />
      )}
    </>
  )
}
