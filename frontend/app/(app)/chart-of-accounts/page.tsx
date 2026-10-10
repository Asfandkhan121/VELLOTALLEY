'use client'

import { BookOpen } from 'lucide-react'
import { Skeleton } from '@/components/ui/skeleton'
import { EmptyState, ErrorState, PageHeader } from '@/components/shared/states'
import { useAccountHeads } from '@/lib/hooks'
import type { AccountHead } from '@/lib/types'

// Read-only reference list. Nothing here assigns or changes a transaction's
// category yet; classification is a later phase.
function groupByMainHead(heads: AccountHead[]) {
  const groups = new Map<string, string[]>()
  for (const { main_head, sub_head } of heads) {
    groups.set(main_head, [...(groups.get(main_head) ?? []), sub_head])
  }
  return [...groups.entries()]
}

export default function ChartOfAccountsPage() {
  const { data, error, isLoading, mutate } = useAccountHeads()
  const groups = groupByMainHead(data ?? [])

  return (
    <>
      <PageHeader
        title="Chart of accounts"
        description="The Main Heads and Sub Heads used to organize transactions. This list is for reference; transactions are not classified automatically yet."
      />

      {error ? (
        <ErrorState error={error} title="Could not load the chart of accounts" onRetry={() => mutate()} />
      ) : isLoading ? (
        <div className="grid gap-4 md:grid-cols-2">
          <Skeleton className="h-40 w-full rounded-xl" />
          <Skeleton className="h-40 w-full rounded-xl" />
        </div>
      ) : groups.length === 0 ? (
        <EmptyState
          icon={BookOpen}
          title="No account heads yet"
          description="The chart of accounts has not been loaded."
        />
      ) : (
        <div className="grid gap-4 md:grid-cols-2">
          {groups.map(([mainHead, subHeads]) => (
            <section key={mainHead} className="flex flex-col gap-3 rounded-xl border p-4">
              <h2 className="font-medium">
                {mainHead} <span className="text-sm font-normal text-muted-foreground">({subHeads.length})</span>
              </h2>
              <ul className="flex flex-wrap gap-2">
                {subHeads.map((subHead) => (
                  <li key={subHead} className="rounded-md bg-accent px-2 py-1 text-sm text-accent-foreground">
                    {subHead}
                  </li>
                ))}
              </ul>
            </section>
          ))}
        </div>
      )}
    </>
  )
}
