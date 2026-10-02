'use client'

import { useState } from 'react'
import { useRouter } from 'next/navigation'
import { Loader2, Trash2 } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { createClient } from '@/lib/supabase/client'
import { deleteAccount, errorMessage } from '@/lib/api'

export function AccountDeletionControl() {
  const router = useRouter()
  const [confirming, setConfirming] = useState(false)
  const [confirmation, setConfirmation] = useState('')
  const [pending, setPending] = useState(false)
  const [error, setError] = useState<string | null>(null)

  async function handleDelete(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault()
    if (confirmation !== 'DELETE') return

    setPending(true)
    setError(null)
    let accountDeleted = false

    try {
      await deleteAccount()
      accountDeleted = true
      const { error: signOutError } = await createClient().auth.signOut({ scope: 'local' })
      if (signOutError) throw signOutError
      router.replace('/login?account_deleted=1')
      router.refresh()
    } catch (caught) {
      setError(accountDeleted
        ? "Your account was deleted, but this browser could not clear its session. Close all Vellotalley tabs and clear this site's stored data."
        : errorMessage(caught))
    } finally {
      setPending(false)
    }
  }

  return (
    <div className="flex flex-col items-start gap-4">
      <p className="text-sm text-muted-foreground">
        Permanently delete your account, clients, statements, extracted transactions, notes, and uploaded PDFs.
        This cannot be undone.
      </p>
      {!confirming ? (
        <Button variant="destructive" onClick={() => setConfirming(true)}>
          <Trash2 aria-hidden="true" />
          Delete account
        </Button>
      ) : (
        <form onSubmit={handleDelete} className="flex w-full max-w-md flex-col gap-3">
          <label htmlFor="delete-account-confirmation" className="text-sm font-medium">
            Type DELETE to confirm account closure.
          </label>
          <Input
            id="delete-account-confirmation"
            autoComplete="off"
            autoCapitalize="characters"
            value={confirmation}
            onChange={(event) => setConfirmation(event.target.value)}
            disabled={pending}
            aria-describedby={error ? 'delete-account-error' : undefined}
          />
          {error && (
            <p id="delete-account-error" role="alert" className="text-sm text-destructive">
              {error}
            </p>
          )}
          <div className="flex flex-wrap gap-2">
            <Button type="submit" variant="destructive" disabled={pending || confirmation !== 'DELETE'}>
              {pending ? <Loader2 className="animate-spin" aria-hidden="true" /> : <Trash2 aria-hidden="true" />}
              {pending ? 'Deleting account...' : 'Permanently delete'}
            </Button>
            <Button
              type="button"
              variant="outline"
              disabled={pending}
              onClick={() => {
                setConfirming(false)
                setConfirmation('')
                setError(null)
              }}
            >
              Cancel
            </Button>
          </div>
        </form>
      )}
    </div>
  )
}
