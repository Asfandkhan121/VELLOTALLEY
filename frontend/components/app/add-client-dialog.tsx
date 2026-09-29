'use client'

import { useState } from 'react'
import { Loader2 } from 'lucide-react'
import { toast } from 'sonner'
import { useSWRConfig } from 'swr'
import {
  Dialog,
  DialogClose,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from '@/components/ui/dialog'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { apiKeys, createClient as createClientApi, errorMessage } from '@/lib/api'
import type { Client } from '@/lib/types'

export function AddClientDialog({
  trigger,
  onCreated,
}: {
  trigger: React.ReactElement
  onCreated?: (client: Client) => void
}) {
  const [open, setOpen] = useState(false)
  const [name, setName] = useState('')
  const [submitting, setSubmitting] = useState(false)
  const { mutate } = useSWRConfig()

  async function handleSubmit(event: React.FormEvent) {
    event.preventDefault()
    const trimmed = name.trim()
    if (!trimmed) {
      toast.error('Client name is required')
      return
    }
    setSubmitting(true)
    try {
      const client = await createClientApi(trimmed)
      await mutate(apiKeys.clients)
      toast.success('Client added', { description: client.name })
      setName('')
      setOpen(false)
      onCreated?.(client)
    } catch (error) {
      toast.error('Could not add client', { description: errorMessage(error) })
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger render={trigger} />
      <DialogContent>
        <form onSubmit={handleSubmit} className="flex flex-col gap-4">
          <DialogHeader>
            <DialogTitle>Add client</DialogTitle>
            <DialogDescription>
              Create a client to group their bank statements and conversions.
            </DialogDescription>
          </DialogHeader>
          <div className="flex flex-col gap-2">
            <Label htmlFor="client-name">Client name</Label>
            <Input
              id="client-name"
              name="name"
              value={name}
              onChange={(event) => setName(event.target.value)}
              placeholder="e.g. Acme Ltd"
              autoComplete="off"
              autoFocus
              required
              maxLength={120}
            />
          </div>
          <DialogFooter>
            <DialogClose render={<Button type="button" variant="outline" disabled={submitting} />}>
              Cancel
            </DialogClose>
            <Button type="submit" disabled={submitting}>
              {submitting ? <Loader2 className="animate-spin" aria-hidden="true" /> : null}
              {submitting ? 'Adding…' : 'Add client'}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  )
}
