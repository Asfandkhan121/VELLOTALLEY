import type { Metadata } from 'next'
import Link from 'next/link'
import { AuthShell } from '@/components/auth/auth-shell'
import { SignUpForm } from '@/components/auth/signup-form'

export const metadata: Metadata = { title: 'Create account' }

export default function SignUpPage() {
  return (
    <AuthShell
      title="Create your account"
      description="3 free statement conversions every month."
      footer={
        <>
          {'Already have an account? '}
          <Link href="/login" className="font-medium text-foreground underline-offset-4 hover:underline">
            Log in
          </Link>
        </>
      }
    >
      <SignUpForm />
    </AuthShell>
  )
}
