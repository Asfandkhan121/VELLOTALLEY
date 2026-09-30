import type { Metadata } from 'next'
import Link from 'next/link'
import { AuthShell } from '@/components/auth/auth-shell'
import { LoginForm } from '@/components/auth/login-form'
import { safeNextPath } from '@/lib/safe-next'

export const metadata: Metadata = { title: 'Log in' }

export default async function LoginPage({
  searchParams,
}: {
  searchParams: Promise<{ next?: string; expired?: string; error?: string }>
}) {
  const params = await searchParams
  const notice = params.expired
    ? 'Your session expired. Please log in again.'
    : params.error === 'link'
      ? 'That link is invalid or has expired. Please try again.'
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
      <LoginForm next={safeNextPath(params.next)} notice={notice} />
    </AuthShell>
  )
}
