export default function PrivacyPage() {
  return (
    <main className="mx-auto max-w-prose px-6 py-16">
      <h1 className="font-serif text-3xl font-semibold text-slate-900">Privacy &amp; how your data is used</h1>
      <p className="mt-4 text-sm text-slate-500">
        This page describes what actually happens to your data in this
        product today. The bracketed items are decisions that haven&apos;t
        been finalized yet — please replace them before this goes live for
        real customers.
      </p>

      <section className="mt-10 space-y-3">
        <h2 className="font-serif text-xl font-semibold text-slate-900">What we store</h2>
        <p className="text-slate-700">
          When you upload a bank statement, we store the PDF, the
          transactions extracted from it, and any notes you add against it,
          tied to your account. Each account can only see its own clients,
          statements, and transactions — this is enforced at the database
          level, not just in the app.
        </p>
      </section>

      <section className="mt-10 space-y-3">
        <h2 className="font-serif text-xl font-semibold text-slate-900">How extraction works</h2>
        <p className="text-slate-700">
          For banks we have a known layout for, extraction happens entirely
          within our own systems — nothing leaves our infrastructure.
        </p>
        <p className="text-slate-700">
          If you choose <strong>Auto-detect</strong>, or upload a statement
          from a bank we don&apos;t have a layout for, we first try an
          automated best-effort extraction ourselves. If that extraction
          isn&apos;t confident enough to trust, the statement is sent to a
          third-party AI provider for extraction instead. Rows produced this
          way are always marked{" "}
          <span className="rounded bg-amber-50 px-1.5 py-0.5 text-amber-700">needs review</span>{" "}
          so you know to double-check them before relying on the figures.
        </p>
        <p className="text-slate-700">
          [Name of AI provider] processes the statement content solely to
          extract transactions and does not use it to train their models.
          [Confirm this against the provider&apos;s actual data-use terms
          before publishing.]
        </p>
      </section>

      <section className="mt-10 space-y-3">
        <h2 className="font-serif text-xl font-semibold text-slate-900">How long we keep it</h2>
        <p className="text-slate-700">
          [Retention period not yet decided — e.g. "for as long as your
          account is active" or a fixed number of days after conversion.]
          You can request deletion of a statement and its transactions at
          any time by [contact method not yet decided].
        </p>
      </section>

      <section className="mt-10 space-y-3">
        <h2 className="font-serif text-xl font-semibold text-slate-900">Questions</h2>
        <p className="text-slate-700">
          Reach us at [support email not yet decided].
        </p>
      </section>
    </main>
  );
}
