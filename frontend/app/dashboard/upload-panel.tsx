"use client";

import { useState } from "react";
import {
  createClientRecord,
  uploadStatement,
  ApiError,
  BANK_PROFILES,
  type Client,
  type Statement,
} from "@/lib/api";

const NEW_CLIENT_VALUE = "__new__";

export function UploadPanel({
  clients,
  onClientCreated,
  onUploaded,
}: {
  clients: Client[];
  onClientCreated: (client: Client) => void;
  onUploaded: (statement: Statement) => void;
}) {
  const [clientId, setClientId] = useState<string>(clients[0]?.id ?? NEW_CLIENT_VALUE);
  const [newClientName, setNewClientName] = useState("");
  const [bankProfile, setBankProfile] = useState(BANK_PROFILES[0].value);
  const [file, setFile] = useState<File | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const isNewClient = clientId === NEW_CLIENT_VALUE;

  async function handleSubmit(event: React.FormEvent) {
    event.preventDefault();
    setError(null);

    if (!file) {
      setError("Choose a PDF statement to upload.");
      return;
    }
    if (isNewClient && !newClientName.trim()) {
      setError("Enter a name for the new client.");
      return;
    }

    setSubmitting(true);
    try {
      let resolvedClientId = clientId;
      if (isNewClient) {
        const created = await createClientRecord(newClientName.trim());
        onClientCreated(created);
        resolvedClientId = created.id;
      }

      const statement = await uploadStatement({ clientId: resolvedClientId, bankProfile, file });
      onUploaded(statement);

      setFile(null);
      setNewClientName("");
      (event.target as HTMLFormElement).reset();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Could not upload the statement.");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="rounded-xl border border-slate-200 bg-white p-6 shadow-sm">
      <h2 className="text-base font-semibold">Convert a statement</h2>
      <form onSubmit={handleSubmit} className="mt-4 space-y-4">
        <div>
          <label htmlFor="client" className="block text-sm font-medium text-slate-700">
            Client
          </label>
          <select
            id="client"
            value={clientId}
            onChange={(e) => setClientId(e.target.value)}
            className="mt-1.5 w-full rounded-md border border-slate-300 px-3 py-2 text-sm text-slate-900 focus:border-ledger-600"
          >
            {clients.map((c) => (
              <option key={c.id} value={c.id}>
                {c.name}
              </option>
            ))}
            <option value={NEW_CLIENT_VALUE}>+ Add a new client</option>
          </select>
          {isNewClient ? (
            <input
              type="text"
              value={newClientName}
              onChange={(e) => setNewClientName(e.target.value)}
              placeholder="Client name"
              className="mt-2 w-full rounded-md border border-slate-300 px-3 py-2 text-sm text-slate-900 placeholder:text-slate-400 focus:border-ledger-600"
            />
          ) : null}
        </div>

        <div>
          <label htmlFor="bank-profile" className="block text-sm font-medium text-slate-700">
            Bank
          </label>
          <select
            id="bank-profile"
            value={bankProfile}
            onChange={(e) => setBankProfile(e.target.value)}
            className="mt-1.5 w-full rounded-md border border-slate-300 px-3 py-2 text-sm text-slate-900 focus:border-ledger-600"
          >
            {BANK_PROFILES.map((b) => (
              <option key={b.value} value={b.value}>
                {b.label}
              </option>
            ))}
          </select>
          {bankProfile === "auto" ? (
            <p className="mt-2 rounded-md bg-amber-50 px-3 py-2 text-xs text-amber-700">
              Auto-detect may send this statement to a third-party AI service
              for extraction if our own attempt isn&apos;t confident enough.
              Rows produced this way are always marked for review. See our{" "}
              <a href="/privacy" className="underline">
                privacy page
              </a>{" "}
              for details.
            </p>
          ) : null}
        </div>

        <div>
          <label htmlFor="file" className="block text-sm font-medium text-slate-700">
            Statement PDF
          </label>
          <input
            id="file"
            type="file"
            accept="application/pdf"
            onChange={(e) => setFile(e.target.files?.[0] ?? null)}
            className="mt-1.5 w-full text-sm text-slate-600 file:mr-3 file:rounded-md file:border-0 file:bg-slate-100 file:px-3 file:py-2 file:text-sm file:font-medium file:text-slate-700 hover:file:bg-slate-200"
          />
        </div>

        {error ? <p className="text-sm text-red-700">{error}</p> : null}

        <button
          type="submit"
          disabled={submitting}
          className="w-full rounded-md bg-ledger-600 px-4 py-2.5 text-sm font-medium text-white hover:bg-ledger-700 disabled:cursor-not-allowed disabled:opacity-60"
        >
          {submitting ? "Uploading…" : "Convert"}
        </button>
      </form>
    </div>
  );
}
