import Link from "next/link";
import { createClient } from "@/lib/supabase/server";
import { BANK_PROFILES } from "@/lib/api";

export default async function LandingPage() {
  const supabase = await createClient();
  const {
    data: { session },
  } = await supabase.auth.getSession();
  const ctaHref = session ? "/dashboard" : "/login";

  return (
    <main>
      {/* Hero */}
      <section className="mx-auto max-w-6xl px-6 pb-20 pt-16 sm:pt-24">
        <div className="grid items-center gap-16 lg:grid-cols-[1fr_1fr]">
          <div>
            <h1 className="max-w-md font-serif text-4xl font-semibold leading-[1.1] tracking-tight text-slate-900 sm:text-5xl">
              Every line of the statement, in a spreadsheet you can trust.
            </h1>
            <p className="mt-6 max-w-md text-lg leading-relaxed text-slate-600">
              Upload a bank statement PDF. VELLOTALLEY extracts the transactions,
              checks every running balance, and hands you back a clean
              workbook — with anything uncertain flagged, not guessed at.
            </p>
            <div className="mt-8 flex items-center gap-4">
              <Link
                href={ctaHref}
                className="rounded-md bg-ledger-600 px-5 py-2.5 text-sm font-medium text-white hover:bg-ledger-700"
              >
                {session ? "Go to your workspace" : "Get started"}
              </Link>
              <a href="#how-it-works" className="text-sm font-medium text-slate-600 hover:text-slate-900">
                See how it works
              </a>
            </div>
          </div>

          {/* Before/after device: a dense, unstructured PDF snippet giving
              way to the actual output table shape, offset and layered
              rather than illustrated with an arrow icon. */}
          <div className="relative mx-auto h-[360px] w-full max-w-md">
            <div
              aria-hidden
              className="absolute left-0 top-4 w-72 -rotate-3 rounded-lg border border-slate-200 bg-slate-50 p-5 shadow-sm"
            >
              <p className="mb-3 text-xs text-slate-400">statement.pdf</p>
              <div className="space-y-2 font-mono text-[11px] leading-relaxed text-slate-400">
                <p>DEP CHQ CLEARING...... 45,000.00</p>
                <p>PROFIT PD A/C 0027013.. 8,926.68</p>
                <p>TAX DEDUCTION ON A/C... 3,570.67</p>
                <p>BAL FWD..... ............195,324.85</p>
                <p>WHT CHGS/SOA FED........... 4.80</p>
              </div>
            </div>

            <div className="absolute bottom-0 right-0 w-80 rounded-lg border border-slate-200 bg-white shadow-md">
              <table className="w-full text-left text-xs">
                <thead>
                  <tr className="border-b border-slate-100 text-slate-500">
                    <th className="px-3 py-2 font-medium">Date</th>
                    <th className="px-3 py-2 font-medium">Description</th>
                    <th className="px-3 py-2 font-medium text-right">Balance</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
                  <tr>
                    <td className="px-3 py-2 text-slate-700">31-12-25</td>
                    <td className="px-3 py-2 text-slate-700">Profit paid to account</td>
                    <td className="px-3 py-2 text-right text-slate-700">195,324.85</td>
                  </tr>
                  <tr className="bg-amber-50">
                    <td className="px-3 py-2 text-slate-700">31-12-25</td>
                    <td className="px-3 py-2 text-slate-700">Tax deduction on account</td>
                    <td className="px-3 py-2 text-right text-slate-700">191,754.18</td>
                  </tr>
                  <tr>
                    <td className="px-3 py-2 text-slate-700">02-01-26</td>
                    <td className="px-3 py-2 text-slate-700">Deposit — cheque clearing</td>
                    <td className="px-3 py-2 text-right text-slate-700">236,754.18</td>
                  </tr>
                </tbody>
              </table>
              <p className="border-t border-slate-100 px-3 py-2 text-[11px] text-amber-700">
                Amber row: balance couldn&apos;t be confirmed from the source — flagged for review, not guessed.
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* How it works — a genuine sequence, so numbered steps are earned here */}
      <section id="how-it-works" className="border-t border-slate-100 bg-slate-50">
        <div className="mx-auto max-w-6xl px-6 py-16">
          <h2 className="font-serif text-2xl font-semibold text-slate-900">How it works</h2>
          <div className="mt-10 grid gap-10 sm:grid-cols-3">
            <Step n={1} title="Upload the PDF">
              Pick a client, choose the bank (or let VELLOTALLEY detect it), and
              drop in the statement.
            </Step>
            <Step n={2} title="Review what's flagged">
              Every transaction is checked against the statement&apos;s own
              running balance. Anything that doesn&apos;t reconcile is
              highlighted, not silently accepted.
            </Step>
            <Step n={3} title="Download the workbook">
              A formatted Excel file, ready for reconciliation — same
              columns, same totals, every time.
            </Step>
          </div>
        </div>
      </section>

      {/* Real bank list, pulled from the same constant the upload form uses */}
      <section className="mx-auto max-w-6xl px-6 py-16">
        <h2 className="font-serif text-2xl font-semibold text-slate-900">Built for the layouts you actually get</h2>
        <p className="mt-3 max-w-prose text-slate-600">
          Each bank formats its statements differently. VELLOTALLEY reads the
          exact column positions for the banks below; anything else goes
          through automatic detection, with extra review built in.
        </p>
        <ul className="mt-8 flex flex-wrap gap-2">
          {BANK_PROFILES.filter((b) => b.value !== "auto").map((bank) => (
            <li
              key={bank.value}
              className="rounded-full border border-slate-200 px-3.5 py-1.5 text-sm text-slate-700"
            >
              {bank.label}
            </li>
          ))}
        </ul>
      </section>

      {/* Accuracy / trust, grounded in the actual validation rule */}
      <section className="border-t border-slate-100 bg-slate-50">
        <div className="mx-auto max-w-6xl px-6 py-16">
          <div className="max-w-prose">
            <h2 className="font-serif text-2xl font-semibold text-slate-900">
              The balance has to add up — or the row gets flagged
            </h2>
            <p className="mt-4 text-slate-600">
              For every transaction, VELLOTALLEY checks that the previous
              balance, minus the debit, plus the credit, equals the new
              balance printed on the statement. When it doesn&apos;t — a
              torn page, a missing figure, an unusual layout — that row is
              marked for review instead of being quietly written into your
              workbook.
            </p>
          </div>
        </div>
      </section>

      <section className="mx-auto max-w-6xl px-6 py-20 text-center">
        <h2 className="font-serif text-2xl font-semibold text-slate-900">Ready to convert your first statement?</h2>
        <Link
          href={ctaHref}
          className="mt-6 inline-block rounded-md bg-ledger-600 px-5 py-2.5 text-sm font-medium text-white hover:bg-ledger-700"
        >
          {session ? "Go to your workspace" : "Get started"}
        </Link>
      </section>
    </main>
  );
}

function Step({ n, title, children }: { n: number; title: string; children: React.ReactNode }) {
  return (
    <div>
      <div className="flex h-8 w-8 items-center justify-center rounded-full bg-ledger-600 text-sm font-medium text-white">
        {n}
      </div>
      <h3 className="mt-4 font-medium text-slate-900">{title}</h3>
      <p className="mt-2 text-sm leading-relaxed text-slate-600">{children}</p>
    </div>
  );
}
