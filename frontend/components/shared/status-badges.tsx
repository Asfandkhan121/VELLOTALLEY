import { AlertTriangle, CheckCircle2, Cpu, FileCog, Loader2, Sparkles, XCircle } from 'lucide-react'
import { cn } from '@/lib/utils'
import {
  confidencePercent,
  confidenceTier,
  methodLabel,
  type DisplayStatus,
} from '@/lib/format'
import type { ExtractionMethod, Statement } from '@/lib/types'

const pillBase =
  'inline-flex items-center gap-1.5 rounded-full border px-2 py-0.5 text-xs font-medium whitespace-nowrap'

const STATUS_CONFIG: Record<DisplayStatus, { label: string; className: string; icon: typeof CheckCircle2 }> = {
  processing: {
    label: 'Processing',
    className: 'border-info/30 bg-info/10 text-info',
    icon: Loader2,
  },
  completed: {
    label: 'Completed',
    className: 'border-success/30 bg-success/10 text-success',
    icon: CheckCircle2,
  },
  needs_review: {
    label: 'Needs review',
    className: 'border-warning/40 bg-warning/10 text-warning-foreground dark:text-warning',
    icon: AlertTriangle,
  },
  failed: {
    label: 'Failed',
    className: 'border-destructive/30 bg-destructive/10 text-destructive',
    icon: XCircle,
  },
}

export function StatusBadge({ status, className }: { status: DisplayStatus; className?: string }) {
  const config = STATUS_CONFIG[status]
  const Icon = config.icon
  return (
    <span className={cn(pillBase, config.className, className)}>
      <Icon className={cn('size-3.5', status === 'processing' && 'animate-spin')} aria-hidden="true" />
      {config.label}
    </span>
  )
}

const METHOD_ICONS: Record<ExtractionMethod, typeof Cpu> = {
  profile: FileCog,
  heuristic: Cpu,
  llm: Sparkles,
}

export function MethodBadge({ method, className }: { method: ExtractionMethod | null; className?: string }) {
  if (!method) return <span className="text-muted-foreground">—</span>
  const Icon = METHOD_ICONS[method] ?? Cpu
  return (
    <span className={cn(pillBase, 'border-border bg-muted/60 text-foreground', className)}>
      <Icon className="size-3.5 text-muted-foreground" aria-hidden="true" />
      {methodLabel(method)}
    </span>
  )
}

const TIER_STYLES = {
  high: { label: 'High', className: 'border-success/30 bg-success/10 text-success' },
  medium: {
    label: 'Medium',
    className: 'border-warning/40 bg-warning/10 text-warning-foreground dark:text-warning',
  },
  low: { label: 'Low', className: 'border-destructive/30 bg-destructive/10 text-destructive' },
} as const

export function ConfidenceBadge({
  confidence,
  className,
}: {
  confidence: Statement['confidence']
  className?: string
}) {
  const percent = confidencePercent(confidence)
  if (percent === null) return <span className="text-muted-foreground">—</span>
  const tier = TIER_STYLES[confidenceTier(percent)]
  return (
    <span className={cn(pillBase, tier.className, className)}>
      <span className="font-mono tabular-nums">{percent}%</span>
      <span className="opacity-80">{tier.label}</span>
    </span>
  )
}
