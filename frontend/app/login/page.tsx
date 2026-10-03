import type { Metadata } from 'next'
import Link from 'next/link'
import { AuthShell } from '@/components/auth/auth-shell'
import { LoginForm } from '@/components/auth/login-form'
import { ResendConfirmationForm } from '@/components/auth/resend-confirmation-form'
import { safeNextPath } from '@/lib/safe-next'

export const metadata: Metadata = { title: 'Log in' }

export default async function LoginPage({
  searchParams,
}: {
  searchParams: Promise<{ next?: string; expired?: string; error?: string; account_deleted?: string }>
}) {
  const params = await searchParams
  const notice = params.account_deleted
    ? 'Your account and associated application data have been deleted.'
    : params.expired
      ? 'Your session expired. Please log in again.'
      : params.error === 'link'
        ? 'The confirmation link could not be completed. It may have expired, already been used, or opened in a different browser. Request a fresh link below and open it in the same browser where you signed up.'
        : null

  return (
    <AuthShell
      title="Welcome back"
      description="Log in to manage your clients and statements."
      footer={
        <>
          {"Don't have an account? "}
          <Link href="/signup" className="font-medium text-foreground underline-offset-4 hover:underline">
            Sign up free
          </Link>
        </>
      }
    >
      <>
        <LoginForm next={safeNextPath(params.next)} notice={notice} />
        {params.error === 'link' && <ResendConfirmationForm />}
      </>
    </AuthShell>
  )
}
