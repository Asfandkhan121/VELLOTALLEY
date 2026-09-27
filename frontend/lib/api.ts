import { createClient } from "@/lib/supabase/client";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";

export class ApiError extends Error {
  status: number;
  constructor(status: number, message: string) {
    super(message);
    this.status = status;
  }
}

async function authHeader(): Promise<Record<string, string>> {
  const supabase = createClient();
  const {
    data: { session },
  } = await supabase.auth.getSession();
  if (!session) throw new ApiError(401, "Not signed in.");
  return { Authorization: `Bearer ${session.access_token}` };
}

async function handle<T>(response: Response): Promise<T> {
  if (!response.ok) {
    let detail = response.statusText;
    try {
      const body = await response.json();
      detail = body.detail ?? detail;
    } catch {
      // response wasn't JSON — keep statusText
    }
    throw new ApiError(response.status, detail);
  }
  return response.json() as Promise<T>;
}

export type Client = { id: string; name: string; created_at: string };

export type Statement = {
  id: string;
  client_id: string;
  original_filename: string;
  bank_profile: string;
  status: "processing" | "extracting" | "completed" | "failed";
  uploaded_at: string;
  extraction_method?: "profile" | "heuristic" | "llm" | null;
  confidence?: number | null;
};

export type Transaction = {
  date: string;
  description: string;
  debit: string | null;
  credit: string | null;
  balance: string | null;
  needs_review: boolean;
};

export async function listClients(): Promise<Client[]> {
  const headers = await authHeader();
  return handle(await fetch(`${API_BASE_URL}/v1/clients`, { headers }));
}

export async function createClientRecord(name: string): Promise<Client> {
  const headers = await authHeader();
  const body = new FormData();
  body.set("name", name);
  return handle(await fetch(`${API_BASE_URL}/v1/clients`, { method: "POST", headers, body }));
}

export async function listStatements(): Promise<Statement[]> {
  const headers = await authHeader();
  return handle(await fetch(`${API_BASE_URL}/v1/statements`, { headers }));
}

export async function getStatement(id: string): Promise<Statement> {
  const headers = await authHeader();
  return handle(await fetch(`${API_BASE_URL}/v1/statements/${id}`, { headers }));
}

export async function uploadStatement(params: {
  clientId: string;
  bankProfile: string;
  file: File;
}): Promise<Statement> {
  const headers = await authHeader();
  const body = new FormData();
  body.set("client_id", params.clientId);
  body.set("bank_profile", params.bankProfile);
  body.set("file", params.file);
  return handle(await fetch(`${API_BASE_URL}/v1/statements`, { method: "POST", headers, body }));
}

export async function extractStatement(id: string): Promise<{ statement_id: string; status: string }> {
  const headers = await authHeader();
  return handle(await fetch(`${API_BASE_URL}/v1/statements/${id}/extract`, { method: "POST", headers }));
}

export async function retryStatement(id: string): Promise<{ statement_id: string; status: string }> {
  const headers = await authHeader();
  return handle(await fetch(`${API_BASE_URL}/v1/statements/${id}/retry`, { method: "POST", headers }));
}

export async function getTransactions(id: string): Promise<Transaction[]> {
  const headers = await authHeader();
  return handle(await fetch(`${API_BASE_URL}/v1/statements/${id}/transactions`, { headers }));
}

export async function downloadExcelUrl(id: string): Promise<string> {
  // FileResponse needs the auth header, which a plain <a href> can't send,
  // so fetch the bytes and hand back an object URL for the caller to open.
  const headers = await authHeader();
  const response = await fetch(`${API_BASE_URL}/v1/statements/${id}/excel`, { headers });
  if (!response.ok) throw new ApiError(response.status, "Could not download the workbook.");
  const blob = await response.blob();
  return URL.createObjectURL(blob);
}

/** Bank profiles the backend currently supports, plus "auto" for anything else. */
export const BANK_PROFILES: { value: string; label: string }[] = [
  { value: "mcb", label: "MCB Bank Limited" },
  { value: "samba", label: "Samba Bank" },
  { value: "fwb", label: "First Women Bank" },
  { value: "ubl", label: "United Bank Limited" },
  { value: "bop", label: "The Bank of Punjab" },
  { value: "allied", label: "Allied Bank" },
  { value: "wio", label: "Wio Bank" },
  { value: "adib", label: "Abu Dhabi Islamic Bank" },
  { value: "aaib", label: "AAIB" },
  { value: "maerki", label: "Maerki Baumann & Co." },
  { value: "pingan", label: "Ping An Bank" },
  { value: "auto", label: "Auto-detect (may use AI, extra review)" },
];
