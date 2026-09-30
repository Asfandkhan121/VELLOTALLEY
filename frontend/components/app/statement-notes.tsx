'use client'

import { useState } from 'react'
import { Loader2, MessageSquarePlus, StickyNote } from 'lucide-react'
import { toast } from 'sonner'
import { Button } from '@/components/ui/button'
import { Textarea } from '@/components/ui/textarea'
import { addNote, apiKeys, errorMessage } from '@/lib/api'
import { formatDateTime } from '@/lib/format'
import { useNotes } from '@/lib/hooks'

export function StatementNotes({ statementId }: { statementId: string }) {
  const { data, isLoading, mutate } = useNotes(statementId)
  const [note, setNote] = useState('')
  const [submitting, setSubmitting] = useState(false)

  const notes = data ?? []

  async function handleSubmit(event: React.FormEvent) {
    event.preventDefault()
    const trimmed = note.trim()
    if (!trimmed) return
    setSubmitting(true)
    try {
      const created = await addNote(statementId, trimmed)
      await mutate((current) => [created, ...(current ?? [])], { revalidate: false })
      setNote('')
      toast.success('Note added')
    } catch (error) {
      toast.error('Could not add note', { description: errorMessage(error) })
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <section aria-label="Review notes" className="flex flex-col gap-4">
      <h2 className="text-lg font-semibold tracking-tight">Review notes</h2>

      <form onSubmit={handleSubmit} className="flex flex-col gap-2">
        <Textarea
          value={note}
          onChange={(event) => setNote(event.target.value)}
          placeholder="Add a note about this statement or its extraction (e.g. rows to double-check)."
          rows={3}
          maxLength={2000}
          disabled={submitting}
        />
        <div className="flex justify-end">
          <Button type="submit" size="sm" disabled={submitting || note.trim().length === 0}>
            {submitting ? (
              <Loader2 className="animate-spin" aria-hidden="true" />
            ) : (
              <MessageSquarePlus aria-hidden="true" />
            )}
            Add note
          </Button>
        </div>
      </form>

      {isLoading ? (
        <p className="text-sm text-muted-foreground">Loading notes…</p>
      ) : notes.length === 0 ? (
        <div className="flex items-center gap-2 rounded-lg border border-dashed px-4 py-6 text-sm text-muted-foreground">
          <StickyNote className="size-4" aria-hidden="true" />
          No notes yet. Add one to keep track of anything worth revisiting.
        </div>
      ) : (
        <ul className="flex flex-col gap-3">
          {notes.map((item) => (
            <li key={item.id} className="rounded-lg border p-3">
              <p className="text-sm whitespace-pre-wrap text-pretty">{item.note}</p>
              <p className="mt-2 text-xs text-muted-foreground">{formatDateTime(item.created_at)}</p>
            </li>
          ))}
        </ul>
      )}
    </section>
  )
}
