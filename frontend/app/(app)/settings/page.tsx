import { Building2, CheckCircle2, Mail, Sparkles } from 'lucide-react'
import { redirect } from 'next/navigation'
import { SignOutButton } from '@/components/app/sign-out-button'
import { AccountDeletionControl } from '@/components/app/account-deletion-control'
import { PageHeader } from '@/components/shared/states'
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card'
import { getBankProfiles } from '@/lib/bank-profiles'
import { createClient } from '@/lib/supabase/server'

export default async function SettingsPage() {
  const supabase = await createClient()
  const {
    data: { user },
  } = await supabase.auth.getUser()
  if (!user) redirect('/login')

  // The "auto detect" option is always present; the rest are configured banks.
  const configuredProfiles = getBankProfiles().filter((profile) => profile.value !== 'auto')

  return (
    <>
      <PageHeader
        title="Settings"
        description="Manage your account, plan, and available bank profiles."
      />

      <Card>
        <CardHeader>
          <CardTitle>Account</CardTitle>
          <CardDescription>The email associated with your Vellotalley account.</CardDescription>
        </CardHeader>
        <CardContent className="flex flex-wrap items-center justify-between gap-4">
          <div className="flex items-center gap-3">
            <span className="flex size-10 items-center justify-center rounded-full bg-accent text-accent-foreground">
              <Mail className="size-4.5" aria-hidden="true" />
            </span>
            <div>
              <p className="text-sm font-medium">{user.email}</p>
              <p className="text-xs text-muted-foreground">Signed in</p>
            </div>
          </div>
          <SignOutButton />
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Plan</CardTitle>
          <CardDescription>Your current subscription and conversion allowance.</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="flex flex-wrap items-center gap-4">
            <span className="flex size-10 items-center justify-center rounded-full bg-accent text-accent-foreground">
              <Sparkles className="size-4.5" aria-hidden="true" />
            </span>
            <div className="flex-1">
              <div className="flex items-center gap-2">
                <p className="text-sm font-medium">Free</p>
                <span className="rounded-full bg-muted px-2 py-0.5 text-xs font-medium text-muted-foreground">
                  Current plan
                </span>
              </div>
              <p className="text-sm text-muted-foreground">Includes 3 statement conversions per month.</p>
            </div>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Bank profiles</CardTitle>
          <CardDescription>
            Configured layouts used to improve extraction accuracy. Statements from other banks fall
            back to automatic detection.
          </CardDescription>
        </CardHeader>
        <CardContent>
          {configuredProfiles.length === 0 ? (
            <div className="flex items-center gap-2 rounded-lg border border-dashed px-4 py-6 text-sm text-muted-foreground">
              <Building2 className="size-4" aria-hidden="true" />
              No dedicated bank profiles are configured. All statements use automatic detection.
            </div>
          ) : (
            <ul className="grid gap-2 sm:grid-cols-2">
              {configuredProfiles.map((profile) => (
                <li
                  key={profile.value}
                  className="flex items-center gap-2.5 rounded-lg border px-3 py-2.5 text-sm"
                >
                  <CheckCircle2 className="size-4 shrink-0 text-success" aria-hidden="true" />
                  <span className="font-medium">{profile.label}</span>
                </li>
              ))}
            </ul>
          )}
        </CardContent>
      </Card>

      <Card className="border-destructive/40">
        <CardHeader>
          <CardTitle>Delete account</CardTitle>
          <CardDescription>
            Close your account and remove its stored application data.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <AccountDeletionControl />
        </CardContent>
      </Card>
    </>
  )
}
