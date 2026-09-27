import type { Statement } from "@/lib/api";

const STYLES: Record<Statement["status"], { label: string; className: string }> = {
  processing: { label: "Processing", className: "bg-slate-100 text-slate-600" },
  extracting: { label: "Extracting", className: "bg-blue-50 text-blue-700" },
  completed: { label: "Completed", className: "bg-ledger-50 text-ledger-700" },
  failed: { label: "Failed", className: "bg-red-50 text-red-700" },
};

export function StatusBadge({ status }: { status: Statement["status"] }) {
  const style = STYLES[status];
  return (
    <span className={`rounded-full px-2.5 py-1 text-xs font-medium ${style.className}`}>
      {style.label}
    </span>
  );
}
