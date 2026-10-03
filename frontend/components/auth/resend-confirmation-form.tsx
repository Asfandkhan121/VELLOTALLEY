'use client'

import { useState } from 'react'
import { Loader2, MailCheck } from 'lucide-react'
import { FormError } from '@/components/auth/auth-shell'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { authRedirectUrl, signUpErrorMessage } from '@/lib/auth-errors'
import { createClient } from '@/lib/supabase/client'

export function ResendConfirmationForm() {
  const [email, setEmail] = useState('')
  const [pending, setPending] = useState(false)
  const [sent, setSent] = useState(false)
  const [error, setError] = useState<string | null>(null)

  async function handleSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault()
    setPending(true)
    setSent(false)
    setError(null)
    try {
      const { error: resendError } = await createClient().auth.resend({
        type: 'signup',
        email: email.trim(),
        options: { emailRedirectTo: authRedirectUrl('/dashboard') },
      })
      if (resendError) {
        setError(signUpErrorMessage(resendError))
        return
      }
      setSent(true)
    } catch {
      setError('Could not reach the authentication service. Check your connection and try again.')
    } finally {
      setPending(false)
    }
  }

  return (
    <form onSubmit={handleSubmit} className="flex flex-col gap-3 border-t pt-4">
      <div className="flex flex-col gap-1">
        <p className="text-sm font-medium">Request a fresh confirmation email</p>
        <p className="text-xs text-muted-foreground">
          Open the new link in the same browser where you signed up. For local preview, use localhost or
          127.0.0.1, not 0.0.0.0.
        </p>
      </div>
      <div className="flex flex-col gap-2">
        <Label htmlFor="confirmation-email">Email</Label>
        <Input
          id="confirmation-email"
          type="email"
          autoComplete="email"
          required
          value={email}
          onChange={(event) => setEmail(event.target.value)}
          placeholder="you@firm.com"
          disabled={pending}
        />
      </div>
      <FormError message={error} />
      {sent && (
        <p role="status" className="flex items-center gap-2 text-sm text-muted-foreground">
          <MailCheck className="size-4" aria-hidden="true" />
          If that address has an unconfirmed account, a fresh link is on its way.
        </p>
      )}
      <Button type="submit" variant="outline" disabled={pending} className="w-full">
        {pending ? <Loader2 className="animate-spin" aria-hidden="true" /> : null}
        {pending ? 'Sending...' : 'Resend confirmation email'}
      </Button>
    </form>
  )
}
