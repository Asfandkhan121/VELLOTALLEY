import type { Transaction } from "@/lib/api";

function money(value: string | null): string {
  return value === null ? "—" : value;
}

export function TransactionTable({ transactions }: { transactions: Transaction[] }) {
  if (transactions.length === 0) {
    return <p className="text-sm text-slate-500">No transactions were extracted from this statement.</p>;
  }

  const flaggedCount = transactions.filter((t) => t.needs_review).length;

  return (
    <div>
      {flaggedCount > 0 ? (
        <p className="mb-3 text-sm text-amber-700">
          {flaggedCount} row{flaggedCount === 1 ? "" : "s"} flagged for review — highlighted below.
        </p>
      ) : null}
      <div className="overflow-x-auto rounded-lg border border-slate-200">
        <table className="w-full text-left text-sm">
          <thead>
            <tr className="border-b border-slate-200 bg-slate-50 text-slate-600">
              <th className="whitespace-nowrap px-4 py-2.5 font-medium">Date</th>
              <th className="px-4 py-2.5 font-medium">Description</th>
              <th className="whitespace-nowrap px-4 py-2.5 text-right font-medium">Debit</th>
              <th className="whitespace-nowrap px-4 py-2.5 text-right font-medium">Credit</th>
              <th className="whitespace-nowrap px-4 py-2.5 text-right font-medium">Balance</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100">
            {transactions.map((t, i) => (
              <tr key={i} className={t.needs_review ? "bg-amber-50" : undefined}>
                <td className="whitespace-nowrap px-4 py-2.5 text-slate-700">{t.date}</td>
                <td className="px-4 py-2.5 text-slate-700">{t.description}</td>
                <td className="whitespace-nowrap px-4 py-2.5 text-right text-slate-700">{money(t.debit)}</td>
                <td className="whitespace-nowrap px-4 py-2.5 text-right text-slate-700">{money(t.credit)}</td>
                <td className="whitespace-nowrap px-4 py-2.5 text-right text-slate-700">{money(t.balance)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
