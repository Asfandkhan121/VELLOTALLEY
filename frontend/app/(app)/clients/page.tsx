'use client'

import Link from 'next/link'
import { FileText, Plus, Users } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Skeleton } from '@/components/ui/skeleton'
import { AddClientDialog } from '@/components/app/add-client-dialog'
import { EmptyState, ErrorState, PageHeader } from '@/components/shared/states'
import { useClients } from '@/lib/hooks'
import { formatDate } from '@/lib/format'

export default function ClientsPage() {
  const { data, error, isLoading, mutate } = useClients()
  const clients = data ?? []

  return (
    <>
      <PageHeader
        title="Clients"
        description="Clients keep each business's bank statements and conversions organized in one place."
        actions={
          <AddClientDialog
            trigger={
              <Button>
                <Plus aria-hidden="true" />
                Add client
              </Button>
            }
          />
        }
      />

      {error ? (
        <ErrorState error={error} title="Could not load clients" onRetry={() => mutate()} />
      ) : isLoading ? (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          <Skeleton className="h-24 w-full rounded-xl" />
          <Skeleton className="h-24 w-full rounded-xl" />
          <Skeleton className="h-24 w-full rounded-xl" />
        </div>
      ) : clients.length === 0 ? (
        <EmptyState
          icon={Users}
          title="No clients yet"
          description="Create your first client to start organizing bank statements and conversions."
          action={
            <AddClientDialog
              trigger={
                <Button>
                  <Plus aria-hidden="true" />
                  Add client
                </Button>
              }
            />
          }
        />
      ) : (
        <ul className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {clients.map((client) => (
            <li
              key={client.id}
              className="flex flex-col gap-4 rounded-xl border p-4 transition-colors hover:border-foreground/20"
            >
              <div className="flex items-start gap-3">
                <span className="flex size-9 shrink-0 items-center justify-center rounded-lg bg-accent text-accent-foreground">
                  <Users className="size-4.5" aria-hidden="true" />
                </span>
                <div className="min-w-0">
                  <h3 className="truncate font-medium" title={client.name}>
                    {client.name}
                  </h3>
                  <p className="text-xs text-muted-foreground">
                    Added {formatDate(client.created_at)}
                  </p>
                </div>
              </div>
              <Button
                variant="outline"
                size="sm"
                className="justify-start"
                render={<Link href={`/statements?client=${client.id}`} />}
              >
                <FileText aria-hidden="true" />
                View statements
              </Button>
            </li>
          ))}
        </ul>
      )}
    </>
  )
}
