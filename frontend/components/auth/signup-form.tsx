'use client'

import { useState } from 'react'
import { useRouter } from 'next/navigation'
import { Loader2, MailCheck } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { FormError } from '@/components/auth/auth-shell'
import { authRedirectUrl, signUpErrorMessage } from '@/lib/auth-errors'
import { createClient } from '@/lib/supabase/client'

export function SignUpForm() {
  const router = useRouter()
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [confirm, setConfirm] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [pending, setPending] = useState(false)
  const [sentTo, setSentTo] = useState<string | null>(null)

  async function handleSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault()
    setError(null)
    if (password.length < 8) {
      setError('Password must be at least 8 characters.')
      return
    }
    if (password !== confirm) {
      setError('Passwords do not match.')
      return
    }
    setPending(true)
    const supabase = createClient()
    const trimmedEmail = email.trim()
    const { data, error: signUpError } = await supabase.auth.signUp({
      email: trimmedEmail,
      password,
      options: { emailRedirectTo: authRedirectUrl('/dashboard') },
    })
    setPending(false)
    if (signUpError) {
      setError(signUpErrorMessage(signUpError))
      return
    }
    if (data.session) {
      router.replace('/dashboard')
      router.refresh()
      return
    }
    setSentTo(trimmedEmail)
  }

  if (sentTo) {
    return (
      <div className="flex flex-col items-center gap-3 text-center" role="status">
        <div className="flex size-11 items-center justify-center rounded-full bg-accent text-accent-foreground">
          <MailCheck className="size-5" aria-hidden="true" />
        </div>
        <p className="font-medium">Check your inbox</p>
        <p className="text-sm text-muted-foreground text-pretty">
          {'If an account can be created for '}
          <span className="font-medium text-foreground">{sentTo}</span>
          {", you'll receive a confirmation link. Open it to activate your account."}
        </p>
      </div>
    )
  }

  return (
    <form onSubmit={handleSubmit} className="flex flex-col gap-4">
      <div className="flex flex-col gap-2">
        <Label htmlFor="email">Work email</Label>
        <Input
          id="email"
          type="email"
          autoComplete="email"
          required
          value={email}
          onChange={(event) => setEmail(event.target.value)}
          placeholder="you@firm.com"
        />
      </div>
      <div className="flex flex-col gap-2">
        <Label htmlFor="password">Password</Label>
        <Input
          id="password"
          type="password"
          autoComplete="new-password"
          required
          minLength={8}
          value={password}
          onChange={(event) => setPassword(event.target.value)}
          aria-describedby="password-hint"
        />
        <p id="password-hint" className="text-xs text-muted-foreground">At least 8 characters.</p>
      </div>
      <div className="flex flex-col gap-2">
        <Label htmlFor="confirm">Confirm password</Label>
        <Input
          id="confirm"
          type="password"
          autoComplete="new-password"
          required
          value={confirm}
          onChange={(event) => setConfirm(event.target.value)}
        />
      </div>
      <FormError message={error} />
      <Button type="submit" disabled={pending} className="w-full">
        {pending ? <Loader2 className="animate-spin" aria-hidden="true" /> : null}
        {pending ? 'Creating account…' : 'Create account'}
      </Button>
    </form>
  )
}
