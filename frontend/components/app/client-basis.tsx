'use client'

import { useState } from 'react'
import { Loader2 } from 'lucide-react'
import { toast } from 'sonner'
import { useSWRConfig } from 'swr'
import { Button } from '@/components/ui/button'
import { ErrorState, PageHeader } from '@/components/shared/states'
import { apiKeys, errorMessage, recommendClientBasis, setClientBasis } from '@/lib/api'
import { useBasisQuestions, useClientBasis } from '@/lib/hooks'
import type { AccountingBasis, BasisRecommendation } from '@/lib/types'

const LABELS: Record<AccountingBasis, string> = {
  accrual: 'Accrual',
  cash: 'Cash',
  modified_cash: 'Modified cash',
}

export function ClientBasis({ clientId }: { clientId: string }) {
  const { mutate } = useSWRConfig()
  const questions = useBasisQuestions()
  const current = useClientBasis(clientId)
  const [answers, setAnswers] = useState<Record<string, string>>({})
  const [rec, setRec] = useState<BasisRecommendation | null>(null)
  const [choice, setChoice] = useState<AccountingBasis | 'unset'>('unset')
  const [busy, setBusy] = useState(false)

  const qs = questions.data ?? []
  const complete = qs.length > 0 && qs.every((q) => answers[q.id])

  async function onRecommend() {
    setBusy(true)
    try {
      const r = await recommendClientBasis(clientId, answers)
      setRec(r)
      // Pre-select the suggestion, but nothing is saved until the user confirms.
      setChoice(r.recommendation ?? 'unset')
    } catch (e) {
      toast.error(errorMessage(e))
    } finally {
      setBusy(false)
    }
  }

  async function onConfirm() {
    setBusy(true)
    try {
      await setClientBasis(clientId, choice)
      await mutate(apiKeys.clientBasis(clientId))
      toast.success(choice === 'unset' ? 'Basis left unset' : `Basis confirmed: ${LABELS[choice]}`)
    } catch (e) {
      toast.error(errorMessage(e))
    } finally {
      setBusy(false)
    }
  }

  if (questions.error) {
    return <ErrorState error={questions.error} title="Could not load questions" onRetry={() => questions.mutate()} />
  }

  const saved = current.data?.accounting_basis

  return (
    <>
      <PageHeader
        title="Accounting basis"
        description="Groundwork for the planned Phase 2 workflow; nothing is categorized by it yet. Answer four questions to get a suggestion. The suggestion is only a suggestion: nothing is saved until you confirm, and you can pick any basis or leave it unset."
      />
      <p className="mb-6 text-sm">
        Current basis: <strong>{saved ? LABELS[saved] : 'Unset'}</strong>
      </p>

      <div className="mb-6 flex flex-col gap-5">
        {qs.map((q) => (
          <fieldset key={q.id} className="flex flex-col gap-2">
            <legend className="font-medium">{q.text}</legend>
            {q.options.map((o) => (
              <label key={o.id} className="flex cursor-pointer items-start gap-2 text-sm">
                <input
                  type="radio"
                  name={q.id}
                  className="mt-1"
                  checked={answers[q.id] === o.id}
                  onChange={() => {
                    setAnswers({ ...answers, [q.id]: o.id })
                    setRec(null)
                  }}
                />
                {o.label}
              </label>
            ))}
            <p className="text-xs text-muted-foreground">{q.why}</p>
          </fieldset>
        ))}
      </div>

      <Button onClick={onRecommend} disabled={!complete || busy} variant="outline">
        Get suggestion
      </Button>

      {rec ? (
        <section className="mt-6 flex flex-col gap-3 rounded-xl border p-4">
          <p className="text-sm">
            Suggestion: <strong>{rec.recommendation ? LABELS[rec.recommendation] : 'none'}</strong>. {rec.reason}
          </p>
          <fieldset className="flex flex-col gap-2 text-sm">
            <legend className="font-medium">Set this client&apos;s basis to</legend>
            {(['accrual', 'cash', 'modified_cash', 'unset'] as const).map((b) => (
              <label key={b} className="flex cursor-pointer items-center gap-2">
                <input type="radio" name="basis" checked={choice === b} onChange={() => setChoice(b)} />
                {b === 'unset' ? 'Leave unset (payroll and income rows stay in review)' : LABELS[b]}
              </label>
            ))}
          </fieldset>
          <div>
            <Button onClick={onConfirm} disabled={busy}>
              {busy ? <Loader2 className="animate-spin" aria-hidden="true" /> : null}
              Confirm
            </Button>
          </div>
        </section>
      ) : null}
    </>
  )
}
