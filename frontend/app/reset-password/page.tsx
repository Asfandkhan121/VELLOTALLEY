import type { Metadata } from 'next'
import { redirect } from 'next/navigation'
import { AuthShell } from '@/components/auth/auth-shell'
import { ResetPasswordForm } from '@/components/auth/password-forms'
import { createClient } from '@/lib/supabase/server'

export const metadata: Metadata = { title: 'Choose a new password' }

export default async function ResetPasswordPage() {
  const supabase = await createClient()
  const {
    data: { user },
  } = await supabase.auth.getUser()
  if (!user) redirect('/login?error=link')

  return (
    <AuthShell title="Choose a new password" description="Enter a new password for your account.">
      <ResetPasswordForm />
    </AuthShell>
  )
}
