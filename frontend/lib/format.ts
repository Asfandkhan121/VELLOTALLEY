import type { ExtractionMethod, Statement } from '@/lib/types'

const amountFormatter = new Intl.NumberFormat('en-US', {
  minimumFractionDigits: 2,
  maximumFractionDigits: 2,
})

export function toNumber(value: string | number | null | undefined): number | null {
  if (value === null || value === undefined || value === '') return null
  const parsed = typeof value === 'number' ? value : Number(String(value).replace(/,/g, ''))
  return Number.isFinite(parsed) ? parsed : null
}

export function formatAmount(value: string | number | null | undefined): string {
  const parsed = toNumber(value)
  return parsed === null ? '' : amountFormatter.format(parsed)
}

export function formatDate(value: string | null | undefined): string {
  if (!value) return '—'
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return value
  return date.toLocaleDateString('en-GB', { day: '2-digit', month: 'short', year: 'numeric' })
}

export function formatDateTime(value: string | null | undefined): string {
  if (!value) return '—'
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return value
  return date.toLocaleString('en-GB', {
    day: '2-digit',
    month: 'short',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  })
}

export function formatFileSize(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
  return `${(bytes / (1024 * 1024)).toFixed(2)} MB`
}

/** Backend confidence is a 0–1 ratio; tolerate a 0–100 value defensively. */
export function confidencePercent(value: Statement['confidence']): number | null {
  const parsed = toNumber(value)
  if (parsed === null) return null
  return Math.round(parsed <= 1 ? parsed * 100 : parsed)
}

export type ConfidenceTier = 'high' | 'medium' | 'low'

export function confidenceTier(percent: number): ConfidenceTier {
  if (percent >= 90) return 'high'
  if (percent >= 75) return 'medium'
  return 'low'
}

export const METHOD_LABELS: Record<ExtractionMethod, string> = {
  profile: 'Profile-based',
  heuristic: 'Automatic layout detection',
  llm: 'AI-assisted',
}

export function methodLabel(method: ExtractionMethod | null | undefined): string {
  return method ? METHOD_LABELS[method] ?? method : '—'
}

export function bankLabel(profile: string | null | undefined): string {
  if (!profile) return '—'
  if (profile === 'auto') return 'Auto detect'
  return profile.toUpperCase()
}

export type DisplayStatus = 'processing' | 'completed' | 'failed' | 'needs_review'

/**
 * The list endpoint has no per-transaction review counts, so "needs review" is
 * derived from signals the backend does return: AI-assisted extraction, or an
 * extraction confidence below 90%.
 */
export function displayStatus(statement: Pick<Statement, 'status' | 'extraction_method' | 'confidence'>): DisplayStatus {
  if (statement.status !== 'completed') return statement.status
  const percent = confidencePercent(statement.confidence)
  if (statement.extraction_method === 'llm') return 'needs_review'
  if (percent !== null && percent < 90) return 'needs_review'
  return 'completed'
}
