import type { Metadata } from 'next'
import { SiteFooter } from '@/components/landing/site-footer'
import { SiteHeader } from '@/components/landing/site-header'
import { createClient } from '@/lib/supabase/server'

export const metadata: Metadata = {
  title: 'Privacy',
  description: 'How Vellotalley handles your bank statements and client data.',
}

const SECTIONS = [
  {
    title: 'What we store',
    body: 'Your account email, the clients you create, the statement PDFs you upload, the transactions extracted from them, and any notes you add.',
  },
  {
    title: 'Who can see it',
    body: 'Only you. Every request is tied to your authenticated session and all data is scoped to your account. Uploaded PDFs are held in private storage.',
  },
  {
    title: 'How statements are processed',
    body: 'Statements are parsed using bank profiles or automatic layout detection. When a layout cannot be read with enough confidence, AI-assisted processing may be used to extract the transactions.',
  },
  {
    title: 'Your control',
    body: 'You decide what to upload. Contact support if you would like your account and associated data removed.',
  },
]

export default async function PrivacyPage() {
  const supabase = await createClient()
  const {
    data: { user },
  } = await supabase.auth.getUser()

  return (
    <>
      <SiteHeader signedIn={Boolean(user)} />
      <main className="mx-auto flex max-w-3xl flex-col gap-8 px-4 py-16 sm:px-6">
        <div className="flex flex-col gap-2">
          <h1 className="text-3xl font-semibold tracking-tight">Privacy</h1>
          <p className="text-muted-foreground">How Vellotalley handles financial documents and client data.</p>
        </div>
        {SECTIONS.map((section) => (
          <section key={section.title} className="flex flex-col gap-2">
            <h2 className="text-lg font-medium">{section.title}</h2>
            <p className="leading-relaxed text-muted-foreground">{section.body}</p>
          </section>
        ))}
      </main>
      <SiteFooter />
    </>
  )
}
