import type {
  Client,
  ExtractionResult,
  Statement,
  StatementNote,
  Transaction,
} from '@/lib/types'

const API_BASE = '/api/backend'

export class ApiError extends Error {
  status: number
  detail: string

  constructor(status: number, detail: string) {
    super(detail)
    this.name = 'ApiError'
    this.status = status
    this.detail = detail
  }
}

const FALLBACK_MESSAGES: Record<number, string> = {
  0: 'Network error. Check your connection and try again.',
  401: 'Your session has expired. Please sign in again.',
  404: 'The requested item could not be found.',
  409: 'This action is not available for the statement in its current state.',
  415: 'Only valid PDF statement files can be uploaded.',
  422: 'The request could not be processed.',
  429: 'You have reached the free monthly conversion limit (3 conversions per month). Please try again next month or upgrade your plan when available.',
  502: 'The conversion service could not store or process this request. Please try again shortly.',
  503: 'The conversion service is temporarily unavailable.',
}

export function errorMessage(error: unknown): string {
  if (error instanceof ApiError) {
    if (error.status === 429) return FALLBACK_MESSAGES[429]
    return error.detail || FALLBACK_MESSAGES[error.status] || 'Something went wrong. Please try again.'
  }
  if (error instanceof Error && error.message) return error.message
  return 'Something went wrong. Please try again.'
}

async function parseErrorDetail(response: Response): Promise<string> {
  try {
    const body = await response.json()
    const detail = body?.detail
    if (typeof detail === 'string') return detail
    if (Array.isArray(detail)) {
      const messages = detail.map((item) => item?.msg).filter(Boolean)
      if (messages.length) return messages.join(' ')
    }
  } catch {
    // Non-JSON error body; fall back to the status-based message.
  }
  return FALLBACK_MESSAGES[response.status] ?? `Request failed (${response.status}).`
}

function redirectToLogin() {
  if (typeof window === 'undefined') return
  const next = window.location.pathname + window.location.search
  window.location.assign(`/login?expired=1&next=${encodeURIComponent(next)}`)
}

async function send(path: string, init?: RequestInit): Promise<Response> {
  let response: Response
  try {
    response = await fetch(`${API_BASE}${path}`, { credentials: 'same-origin', ...init })
  } catch {
    throw new ApiError(0, FALLBACK_MESSAGES[0])
  }
  if (!response.ok) {
    const detail = await parseErrorDetail(response)
    if (response.status === 401) redirectToLogin()
    throw new ApiError(response.status, detail)
  }
  return response
}

async function requestJson<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await send(path, init)
  return (await response.json()) as T
}

function formBody(fields: Record<string, string | Blob>) {
  const form = new FormData()
  for (const [key, value] of Object.entries(fields)) form.append(key, value)
  return form
}

export const fetcher = <T,>(path: string) => requestJson<T>(path)

export function createClient(name: string) {
  return requestJson<Client>('/v1/clients', {
    method: 'POST',
    body: formBody({ name: name.trim() }),
  })
}

export function listClients() {
  return requestJson<Client[]>('/v1/clients')
}

export async function deleteAccount() {
  await send('/v1/account', { method: 'DELETE' })
}

export function createStatement(input: { clientId: string; bankProfile: string; file: File }) {
  return requestJson<Statement>('/v1/statements', {
    method: 'POST',
    body: formBody({
      client_id: input.clientId,
      bank_profile: input.bankProfile,
      file: input.file,
    }),
  })
}

export function extractStatement(statementId: string) {
  return requestJson<ExtractionResult>(`/v1/statements/${statementId}/extract`, { method: 'POST' })
}

export function retryStatement(statementId: string) {
  return requestJson<ExtractionResult>(`/v1/statements/${statementId}/retry`, { method: 'POST' })
}

export function listStatements() {
  return requestJson<Statement[]>('/v1/statements')
}

export function getStatement(statementId: string) {
  return requestJson<Statement>(`/v1/statements/${statementId}`)
}

export function getTransactions(statementId: string) {
  return requestJson<Transaction[]>(`/v1/statements/${statementId}/transactions`)
}

export function addNote(statementId: string, note: string) {
  return requestJson<StatementNote>(`/v1/statements/${statementId}/notes`, {
    method: 'POST',
    body: formBody({ note: note.trim() }),
  })
}

export function listNotes(statementId: string) {
  return requestJson<StatementNote[]>(`/v1/statements/${statementId}/notes`)
}

export async function downloadExcel(statementId: string, fallbackName?: string) {
  const response = await send(`/v1/statements/${statementId}/excel`)
  const blob = await response.blob()
  const disposition = response.headers.get('content-disposition') ?? ''
  const match = /filename\*?=(?:UTF-8'')?"?([^";]+)"?/i.exec(disposition)
  const filename = match ? decodeURIComponent(match[1]) : fallbackName ?? `statement-${statementId}.xlsx`

  const url = URL.createObjectURL(blob)
  const anchor = document.createElement('a')
  anchor.href = url
  anchor.download = filename
  document.body.appendChild(anchor)
  anchor.click()
  anchor.remove()
  setTimeout(() => URL.revokeObjectURL(url), 1000)
}

export const apiKeys = {
  clients: '/v1/clients',
  accountHeads: '/v1/account-heads',
  statements: '/v1/statements',
  statement: (id: string) => `/v1/statements/${id}`,
  transactions: (id: string) => `/v1/statements/${id}/transactions`,
  notes: (id: string) => `/v1/statements/${id}/notes`,
}
