import type { Metadata } from 'next'
import { SiteFooter } from '@/components/landing/site-footer'
import { SiteHeader } from '@/components/landing/site-header'
import { createClient } from '@/lib/supabase/server'

export const metadata: Metadata = {
  title: 'Privacy',
  description: 'What Vellotalley collects, how it processes bank statements, and how to delete your data.',
}

const SECTIONS = [
  {
    title: 'Information we collect',
    paragraphs: [
      'We store your account email and identifier; client names; the bank-statement PDFs and filenames you upload; your selected bank profile; extracted transaction dates, descriptions, amounts and balances; statement-processing status and upload time; and notes you choose to save.',
      'When an unsupported bank profile is submitted, the requested profile and your account identifier may be recorded to help plan bank-profile coverage. This signal is not used to train a model or change the parser automatically.',
      'The application uses authentication cookies to keep your session. Production builds include Vercel Web Analytics; whether analytics collection is active depends on the deployment configuration.',
    ],
  },
  {
    title: 'How statements are processed',
    paragraphs: [
      'Statements are processed by configured bank layouts or automatic, server-side layout detection. The separate transaction-text hints are generated locally by the backend and do not change extracted values, extraction confidence, or the human-review flag.',
      'If automatic detection fails or cannot produce a confidence of at least 0.85, the backend uses the configured LLM fallback. The default OpenAI-compatible provider receives extracted statement text in chunks; if Anthropic is explicitly configured instead, it receives the complete PDF. A locally hosted model keeps statement content on the backend machine. This happens automatically without a separate confirmation for each upload. Do not upload a statement unless you are authorized to share it with the service and any configured processing providers.',
    ],
  },
  {
    title: 'Service providers and storage',
    paragraphs: [
      'Supabase provides account authentication, the application database, and private storage for uploaded PDFs. The backend uses authenticated account ownership checks when serving application data.',
      'The configured LLM provider processes statement content only when the automatic fallback described above is triggered. With a hosted provider, the statement text or PDF is sent to that provider; with a self-hosted local model it stays on the backend machine. Vercel Web Analytics is included in production builds, subject to the deployment settings. Hosted providers process information under their own service terms and retention practices.',
    ],
  },
  {
    title: 'Retention and account deletion',
    paragraphs: [
      `Your application data in Vellotalley's active systems is kept while your account is active. To close your account, use Settings > Delete account. The service removes your uploaded PDFs, account-owned records (including clients, statements, transactions, notes, and bank-demand signals), and then the authentication account.`,
      `Deletion spans separate storage, database, and authentication systems and cannot be completed as one transaction. If any step fails, the service reports that deletion may be partial; contact us before retrying. Copies held by processing providers or in their backups may remain under those providers' retention practices.`,
    ],
  },
  {
    title: 'Your choices and contact',
    paragraphs: [
      'You can choose not to upload a document, and you can request help with access, correction, or deletion. Rows flagged for review should be checked by a person before you rely on them for accounting decisions.',
    ],
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
          <p className="text-muted-foreground">
            What Vellotalley collects and how financial documents and account data are handled.
          </p>
        </div>
        {SECTIONS.map((section) => (
          <section key={section.title} className="flex flex-col gap-2">
            <h2 className="text-lg font-medium">{section.title}</h2>
            {section.paragraphs.map((paragraph) => (
              <p key={paragraph} className="leading-relaxed text-muted-foreground">
                {paragraph}
              </p>
            ))}
            {section.title === 'Your choices and contact' && (
              <p className="leading-relaxed text-muted-foreground">
                Contact <a className="underline underline-offset-4" href="mailto:HELP@VELLOTALLEY.COM">HELP@VELLOTALLEY.COM</a>.
              </p>
            )}
          </section>
        ))}
      </main>
      <SiteFooter />
    </>
  )
}
