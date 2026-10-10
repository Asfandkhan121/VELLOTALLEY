import Link from 'next/link'
import {
  ArrowRight,
  Building2,
  FileSpreadsheet,
  FolderKanban,
  Lock,
  ScanSearch,
  ShieldCheck,
  StickyNote,
  Upload,
  UserCheck,
} from 'lucide-react'
import { Button } from '@/components/ui/button'
import { PhaseJourney } from '@/components/shared/phase-journey'

function SectionHeading({ eyebrow, title, description }: { eyebrow: string; title: string; description: string }) {
  return (
    <div className="flex max-w-2xl flex-col gap-3">
      <p className="text-sm font-medium text-primary">{eyebrow}</p>
      <h2 className="text-3xl font-semibold tracking-tight text-balance">{title}</h2>
      <p className="text-muted-foreground leading-relaxed text-pretty">{description}</p>
    </div>
  )
}

const STEPS = [
  { icon: Building2, title: 'Pick a client', text: 'Create or select the client the statement belongs to.' },
  { icon: Upload, title: 'Upload the PDF', text: 'Choose the bank profile, or let Vellotalley detect the layout.' },
  { icon: ScanSearch, title: 'Review the rows', text: 'Check extracted transactions — uncertain rows are flagged.' },
  { icon: FileSpreadsheet, title: 'Download Excel', text: 'Export a structured spreadsheet for your workpapers.' },
]

export function HowItWorks() {
  return (
    <section id="how-it-works" className="scroll-mt-20 border-b">
      <div className="mx-auto flex max-w-6xl flex-col gap-10 px-4 py-16 sm:px-6 md:py-20">
        <SectionHeading
          eyebrow="How it works"
          title="From statement to spreadsheet in four steps"
          description="No templates to build and no copying rows by hand. Each conversion stays organised under the client it belongs to."
        />
        <ol className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          {STEPS.map((step, index) => (
            <li key={step.title} className="flex flex-col gap-3 rounded-xl border bg-card p-5">
              <div className="flex items-center justify-between">
                <div className="flex size-9 items-center justify-center rounded-lg bg-accent text-accent-foreground">
                  <step.icon className="size-4" aria-hidden="true" />
                </div>
                <span className="font-mono text-xs text-muted-foreground">0{index + 1}</span>
              </div>
              <h3 className="font-medium">{step.title}</h3>
              <p className="text-sm text-muted-foreground leading-relaxed">{step.text}</p>
            </li>
          ))}
        </ol>
      </div>
    </section>
  )
}

export function ProductRoadmap({ signedIn }: { signedIn: boolean }) {
  return (
    <section id="workflow" className="scroll-mt-20 border-b bg-card/40">
      <div className="mx-auto max-w-6xl px-4 py-16 sm:px-6 md:py-20">
        <PhaseJourney signedIn={signedIn} />
      </div>
    </section>
  )
}

const FEATURES = [
  {
    icon: FolderKanban,
    title: 'Client-based organisation',
    text: 'Every statement is filed under a client, so a month-end batch never turns into a folder of anonymous PDFs.',
  },
  {
    icon: ScanSearch,
    title: 'Three-stage extraction',
    text: 'Bank profiles for known layouts, automatic layout detection for others, and AI-assisted processing when needed.',
  },
  {
    icon: UserCheck,
    title: 'Review flags you can trust',
    text: 'Rows that need a second look are highlighted, with extraction method and confidence shown for every statement.',
  },
  {
    icon: FileSpreadsheet,
    title: 'Clean Excel exports',
    text: 'Date, description, debit, credit and balance — consistent columns you can drop straight into your working files.',
  },
  {
    icon: StickyNote,
    title: 'Statement notes',
    text: 'Leave context for yourself or a reviewer: missing pages, reconciled items, or questions for the client.',
  },
  {
    icon: ShieldCheck,
    title: 'Private by default',
    text: 'Statements are scoped to your account. Other users can never see your clients or their transactions.',
  },
]

export function Features() {
  return (
    <section id="features" className="scroll-mt-20 border-b bg-card/40">
      <div className="mx-auto flex max-w-6xl flex-col gap-10 px-4 py-16 sm:px-6 md:py-20">
        <SectionHeading
          eyebrow="Features"
          title="Designed around how accounting work actually happens"
          description="Vellotalley focuses on one job — turning statements into dependable data — and does it with the audit trail accountants expect."
        />
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {FEATURES.map((feature) => (
            <div key={feature.title} className="flex flex-col gap-3 rounded-xl border bg-card p-5">
              <feature.icon className="size-5 text-primary" aria-hidden="true" />
              <h3 className="font-medium">{feature.title}</h3>
              <p className="text-sm text-muted-foreground leading-relaxed">{feature.text}</p>
            </div>
          ))}
        </div>
      </div>
    </section>
  )
}

const SECURITY_POINTS = [
  'Every request is authenticated against your signed-in session.',
  'Statements, clients and transactions are only returned for the account that owns them.',
  'Uploaded PDFs are stored privately and are never publicly accessible.',
  'Upload validation rejects anything that is not a genuine PDF file.',
]

export function Security() {
  return (
    <section id="security" className="scroll-mt-20 border-b">
      <div className="mx-auto flex max-w-6xl flex-col gap-10 px-4 py-16 sm:px-6 md:flex-row md:items-start md:gap-16 md:py-20">
        <div className="flex-1">
          <SectionHeading
            eyebrow="Security & privacy"
            title="Financial documents deserve careful handling"
            description="Bank statements contain sensitive client information. Vellotalley is built so your data stays yours."
          />
        </div>
        <ul className="flex flex-1 flex-col gap-3">
          {SECURITY_POINTS.map((point) => (
            <li key={point} className="flex items-start gap-3 rounded-xl border bg-card p-4">
              <Lock className="mt-0.5 size-4 shrink-0 text-primary" aria-hidden="true" />
              <span className="text-sm leading-relaxed">{point}</span>
            </li>
          ))}
        </ul>
      </div>
    </section>
  )
}

const FAQS = [
  {
    q: 'Which banks are supported?',
    a: 'Known layouts are converted with dedicated bank profiles. For any other bank, choose “Auto detect” — Vellotalley detects the layout automatically and uses AI-assisted processing if the layout cannot be read with enough confidence.',
  },
  {
    q: 'How many statements can I convert for free?',
    a: 'The free plan includes three conversions per calendar month. The count resets at the start of each month.',
  },
  {
    q: 'What does “needs review” mean?',
    a: 'Some rows or statements are extracted with lower certainty — for example unusual layouts or ambiguous dates. They are highlighted so you can confirm them against the original PDF before relying on them.',
  },
  {
    q: 'Can I use scanned statements?',
    a: 'Vellotalley works best with digital PDFs downloaded from online banking. Scanned or photographed pages may extract poorly or fail.',
  },
  {
    q: 'What if a conversion fails?',
    a: 'You can retry extraction from the statement page at any time. Failed and in-progress statements remain listed so nothing is lost.',
  },
]

export function Faq() {
  return (
    <section id="faq" className="scroll-mt-20 border-b bg-card/40">
      <div className="mx-auto flex max-w-3xl flex-col gap-8 px-4 py-16 sm:px-6 md:py-20">
        <SectionHeading eyebrow="FAQ" title="Common questions" description="Everything you need to know before your first upload." />
        <div className="flex flex-col divide-y rounded-xl border bg-card">
          {FAQS.map((item) => (
            <details key={item.q} className="group px-5 py-4">
              <summary className="flex cursor-pointer list-none items-center justify-between gap-4 font-medium [&::-webkit-details-marker]:hidden">
                {item.q}
                <span className="text-muted-foreground transition-transform group-open:rotate-45" aria-hidden="true">
                  +
                </span>
              </summary>
              <p className="pt-3 text-sm leading-relaxed text-muted-foreground">{item.a}</p>
            </details>
          ))}
        </div>
      </div>
    </section>
  )
}

export function FinalCta({ signedIn }: { signedIn: boolean }) {
  return (
    <section className="border-b">
      <div className="mx-auto flex max-w-6xl flex-col items-start gap-6 px-4 py-16 sm:px-6 md:flex-row md:items-center md:justify-between md:py-20">
        <div className="flex flex-col gap-2">
          <h2 className="text-2xl font-semibold tracking-tight text-balance">Stop retyping bank statements.</h2>
          <p className="text-muted-foreground">Convert your first three statements this month for free.</p>
        </div>
        <Button nativeButton={false} render={<Link href={signedIn ? '/statements/new' : '/signup'} />} size="lg">
          {signedIn ? 'Convert a statement' : 'Create free account'}
          <ArrowRight aria-hidden="true" />
        </Button>
      </div>
    </section>
  )
}
