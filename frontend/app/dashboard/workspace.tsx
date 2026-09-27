"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import {
  listClients,
  listStatements,
  extractStatement,
  retryStatement,
  getStatement,
  getTransactions,
  downloadExcelUrl,
  ApiError,
  type Client,
  type Statement,
  type Transaction,
} from "@/lib/api";
import { UploadPanel } from "./upload-panel";
import { StatusBadge } from "./status-badge";
import { TransactionTable } from "./transaction-table";

const BANK_LABELS: Record<string, string> = {
  mcb: "MCB", samba: "Samba", fwb: "FWB", ubl: "UBL", bop: "BOP",
  allied: "Allied", wio: "Wio", adib: "ADIB", aaib: "AAIB",
  maerki: "Maerki Baumann", pingan: "Ping An", auto: "Auto-detect",
};

export function Workspace() {
  const [clients, setClients] = useState<Client[]>([]);
  const [statements, setStatements] = useState<Statement[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [transactions, setTransactions] = useState<Transaction[] | null>(null);
  const [previewLoading, setPreviewLoading] = useState(false);
  const [banner, setBanner] = useState<string | null>(null);
  const pollHandles = useRef<Record<string, ReturnType<typeof setInterval>>>({});

  const refreshStatements = useCallback(async () => {
    try {
      setStatements(await listStatements());
    } catch {
      // transient — the next poll/refresh will retry
    }
  }, []);

  useEffect(() => {
    (async () => {
      try {
        const [clientList, statementList] = await Promise.all([listClients(), listStatements()]);
        setClients(clientList);
        setStatements(statementList);
      } catch (err) {
        setBanner(err instanceof ApiError ? err.message : "Could not load your workspace.");
      } finally {
        setLoading(false);
      }
    })();
    return () => {
      Object.values(pollHandles.current).forEach(clearInterval);
    };
  }, []);

  function pollUntilDone(statementId: string) {
    if (pollHandles.current[statementId]) return;
    pollHandles.current[statementId] = setInterval(async () => {
      try {
        const updated = await getStatement(statementId);
        setStatements((prev) => prev.map((s) => (s.id === statementId ? updated : s)));
        if (updated.status === "completed" || updated.status === "failed") {
          clearInterval(pollHandles.current[statementId]);
          delete pollHandles.current[statementId];
        }
      } catch {
        // keep polling — a transient failure here shouldn't stop the loop
      }
    }, 2000);
  }

  async function handleUploaded(statement: Statement) {
    setStatements((prev) => [statement, ...prev]);
    setBanner(null);
    try {
      await extractStatement(statement.id);
      pollUntilDone(statement.id);
    } catch (err) {
      setBanner(err instanceof ApiError ? err.message : "Could not start extraction.");
    }
  }

  async function handleRetry(statementId: string) {
    try {
      await retryStatement(statementId);
      pollUntilDone(statementId);
      await refreshStatements();
    } catch (err) {
      setBanner(err instanceof ApiError ? err.message : "Could not retry this statement.");
    }
  }

  async function handlePreview(statementId: string) {
    setSelectedId(statementId);
    setPreviewLoading(true);
    setTransactions(null);
    try {
      setTransactions(await getTransactions(statementId));
    } catch (err) {
      setBanner(err instanceof ApiError ? err.message : "Could not load the preview.");
    } finally {
      setPreviewLoading(false);
    }
  }

  async function handleDownload(statementId: string) {
    try {
      const url = await downloadExcelUrl(statementId);
      const a = document.createElement("a");
      a.href = url;
      a.download = `statement-${statementId}.xlsx`;
      a.click();
      URL.revokeObjectURL(url);
    } catch (err) {
      setBanner(err instanceof ApiError ? err.message : "Could not download the workbook.");
    }
  }

  if (loading) {
    return <p className="p-8 text-sm text-slate-500">Loading…</p>;
  }

  return (
    <div className="mx-auto max-w-5xl space-y-6 px-4 py-8">
      {banner ? (
        <div className="rounded-md bg-red-50 px-4 py-3 text-sm text-red-700">{banner}</div>
      ) : null}

      <div className="grid gap-6 md:grid-cols-[minmax(0,360px)_1fr]">
        <UploadPanel
          clients={clients}
          onClientCreated={(c) => setClients((prev) => [...prev, c])}
          onUploaded={handleUploaded}
        />

        <div className="rounded-xl border border-slate-200 bg-white shadow-sm">
          <div className="flex items-center justify-between border-b border-slate-100 px-6 py-4">
            <h2 className="text-base font-semibold">Your statements</h2>
            <button onClick={refreshStatements} className="text-sm text-slate-500 hover:text-slate-900">
              Refresh
            </button>
          </div>

          {statements.length === 0 ? (
            <p className="px-6 py-8 text-sm text-slate-500">
              No conversions yet — upload a statement to get started.
            </p>
          ) : (
            <ul className="divide-y divide-slate-100">
              {statements.map((s) => (
                <li key={s.id} className="flex items-center justify-between gap-4 px-6 py-3">
                  <div className="min-w-0">
                    <p className="truncate text-sm font-medium">{s.original_filename}</p>
                    <p className="text-xs text-slate-500">
                      {BANK_LABELS[s.bank_profile] ?? s.bank_profile}
                      {s.extraction_method && s.extraction_method !== "profile"
                        ? ` · via ${s.extraction_method}`
                        : ""}
                    </p>
                  </div>
                  <div className="flex items-center gap-3">
                    <StatusBadge status={s.status} />
                    {s.status === "completed" ? (
                      <>
                        <button
                          onClick={() => handlePreview(s.id)}
                          className="text-sm font-medium text-slate-700 hover:text-slate-900"
                        >
                          Preview
                        </button>
                        <button
                          onClick={() => handleDownload(s.id)}
                          className="rounded-md bg-slate-900 px-2.5 py-1 text-sm font-medium text-white hover:bg-slate-800"
                        >
                          Excel
                        </button>
                      </>
                    ) : null}
                    {s.status === "failed" ? (
                      <button
                        onClick={() => handleRetry(s.id)}
                        className="text-sm font-medium text-slate-700 hover:text-slate-900"
                      >
                        Retry
                      </button>
                    ) : null}
                  </div>
                </li>
              ))}
            </ul>
          )}
        </div>
      </div>

      {selectedId ? (
        <div className="rounded-xl border border-slate-200 bg-white p-6 shadow-sm">
          <div className="mb-4 flex items-center justify-between">
            <h2 className="text-base font-semibold">Preview</h2>
            <button onClick={() => setSelectedId(null)} className="text-sm text-slate-500 hover:text-slate-900">
              Close
            </button>
          </div>
          {previewLoading ? (
            <p className="text-sm text-slate-500">Loading transactions…</p>
          ) : (
            <TransactionTable transactions={transactions ?? []} />
          )}
        </div>
      ) : null}
    </div>
  );
}
