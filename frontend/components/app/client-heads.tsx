'use client'

import { useState } from 'react'
import { Loader2 } from 'lucide-react'
import { toast } from 'sonner'
import { useSWRConfig } from 'swr'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { ErrorState, PageHeader } from '@/components/shared/states'
import { apiKeys, confirmClientHeads, errorMessage, proposeClientHeads } from '@/lib/api'
import { useClientHeads } from '@/lib/hooks'
import type { HeadProposalSheet } from '@/lib/types'

export function ClientHeads({ clientId }: { clientId: string }) {
  const { mutate } = useSWRConfig()
  const { data: saved, error, mutate: reload } = useClientHeads(clientId)
  const [sheets, setSheets] = useState<HeadProposalSheet[] | null>(null)
  const [sheetIdx, setSheetIdx] = useState(0)
  const [skipped, setSkipped] = useState<Set<number>>(new Set())
  const [busy, setBusy] = useState(false)

  const sheet = sheets?.[sheetIdx]

  async function onFile(file: File | undefined) {
    if (!file) return
    setBusy(true)
    try {
      const result = await proposeClientHeads(clientId, file)
      setSheets(result)
      setSheetIdx(0)
      setSkipped(new Set())
    } catch (e) {
      toast.error(errorMessage(e))
    } finally {
      setBusy(false)
    }
  }

  async function onConfirm() {
    if (!sheet) return
    const heads = sheet.heads
      .filter((_, i) => !skipped.has(i))
      .map(({ name, section, code }) => ({ name, section, code }))
    if (heads.length === 0) return
    setBusy(true)
    try {
      const r = await confirmClientHeads(clientId, { source: 'trial_balance', heads })
      toast.success(`${r.created} heads saved, ${r.skipped_existing.length} already existed`)
      setSheets(null)
      await mutate(apiKeys.clientHeads(clientId))
    } catch (e) {
      toast.error(errorMessage(e))
    } finally {
      setBusy(false)
    }
  }

  const evidence = sheet ? Object.entries(sheet.evidence) : []

  return (
    <>
      <PageHeader
        title="Account heads"
        description="Upload last year's trial balance (.xlsx). Review the heads found, untick any you don't want, then confirm. Nothing is saved until you confirm."
      />

      <div className="mb-6 flex flex-col gap-2">
        <Input
          type="file"
          accept=".xlsx"
          disabled={busy}
          onChange={(e) => {
            void onFile(e.target.files?.[0])
            e.target.value = ''
          }}
        />
      </div>

      {sheets && sheet ? (
        <section className="mb-8 flex flex-col gap-4 rounded-xl border p-4">
          {sheets.length > 1 ? (
            <div className="flex flex-wrap gap-2">
              {sheets.map((s, i) => (
                <Button
                  key={s.sheet}
                  size="sm"
                  variant={i === sheetIdx ? 'default' : 'outline'}
                  onClick={() => {
                    setSheetIdx(i)
                    setSkipped(new Set())
                  }}
                >
                  {s.sheet}
                </Button>
              ))}
            </div>
          ) : null}
          <p className="text-sm text-muted-foreground">
            {[sheet.entity, sheet.period].filter(Boolean).join(' · ') || sheet.sheet}
          </p>
          {sheet.stated_basis || evidence.length > 0 ? (
            <div className="rounded-lg bg-muted p-3 text-sm">
              <p className="font-medium">Evidence only. It does not set the accounting basis.</p>
              {sheet.stated_basis ? <p>File says: {sheet.stated_basis}</p> : null}
              {evidence.map(([kind, names]) => (
                <p key={kind}>
                  {kind}: {names.slice(0, 3).join(', ')}
                </p>
              ))}
            </div>
          ) : null}
          {sheet.warnings.map((w) => (
            <p key={w} className="text-sm text-destructive">
              {w}
            </p>
          ))}
          {!sheet.hierarchy ? (
            <p className="text-sm text-muted-foreground">
              No indentation found, so group rows may appear as heads. Untick those.
            </p>
          ) : null}
          <ul className="max-h-96 divide-y overflow-auto rounded-lg border">
            {sheet.heads.map((h, i) => (
              <li key={`${h.row}-${h.name}`}>
                <label className="flex cursor-pointer items-center gap-3 px-3 py-2 text-sm">
                  <input
                    type="checkbox"
                    checked={!skipped.has(i)}
                    onChange={() => {
                      const next = new Set(skipped)
                      if (next.has(i)) next.delete(i)
                      else next.add(i)
                      setSkipped(next)
                    }}
                  />
                  <span className="flex-1">{h.name}</span>
                  <span className="text-xs text-muted-foreground">
                    {[h.code, h.section].filter(Boolean).join(' · ')}
                  </span>
                </label>
              </li>
            ))}
          </ul>
          <div className="flex gap-2">
            <Button onClick={onConfirm} disabled={busy || skipped.size === sheet.heads.length}>
              {busy ? <Loader2 className="animate-spin" aria-hidden="true" /> : null}
              Confirm {sheet.heads.length - skipped.size} heads
            </Button>
            <Button variant="outline" onClick={() => setSheets(null)} disabled={busy}>
              Discard
            </Button>
          </div>
        </section>
      ) : null}

      <h2 className="mb-2 font-medium">Confirmed heads{saved ? ` (${saved.length})` : ''}</h2>
      {error ? (
        <ErrorState error={error} title="Could not load heads" onRetry={() => reload()} />
      ) : saved && saved.length === 0 ? (
        <p className="text-sm text-muted-foreground">None yet.</p>
      ) : (
        <ul className="divide-y rounded-lg border">
          {(saved ?? []).map((h) => (
            <li key={h.id} className="flex items-center gap-3 px-3 py-2 text-sm">
              <span className="flex-1">{h.name}</span>
              <span className="text-xs text-muted-foreground">
                {[h.code, h.section].filter(Boolean).join(' · ')}
              </span>
            </li>
          ))}
        </ul>
      )}
    </>
  )
}
