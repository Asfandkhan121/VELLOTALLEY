'use client'

import { useState } from 'react'
import { Download, Loader2, RotateCw } from 'lucide-react'
import { toast } from 'sonner'
import { useSWRConfig } from 'swr'
import { Button } from '@/components/ui/button'
import { apiKeys, downloadExcel, errorMessage, retryStatement } from '@/lib/api'

type ButtonProps = React.ComponentProps<typeof Button>

export function DownloadExcelButton({
  statementId,
  filename,
  label = 'Download Excel',
  ...props
}: { statementId: string; filename?: string; label?: string } & Omit<ButtonProps, 'onClick'>) {
  const [pending, setPending] = useState(false)

  async function handleDownload() {
    setPending(true)
    try {
      const fallback = filename ? `${filename.replace(/\.pdf$/i, '')}.xlsx` : undefined
      await downloadExcel(statementId, fallback)
    } catch (error) {
      toast.error('Download failed', { description: errorMessage(error) })
    } finally {
      setPending(false)
    }
  }

  return (
    <Button onClick={handleDownload} disabled={pending || props.disabled} {...props}>
      {pending ? <Loader2 className="animate-spin" aria-hidden="true" /> : <Download aria-hidden="true" />}
      {pending ? 'Preparing…' : label}
    </Button>
  )
}

export function RetryExtractionButton({
  statementId,
  label = 'Retry extraction',
  onSettled,
  ...props
}: { statementId: string; label?: string; onSettled?: () => void } & Omit<ButtonProps, 'onClick'>) {
  const [pending, setPending] = useState(false)
  const { mutate } = useSWRConfig()

  async function handleRetry() {
    setPending(true)
    const toastId = toast.loading('Retrying extraction…', {
      description: 'This can take a minute for longer statements.',
    })
    try {
      const result = await retryStatement(statementId)
      toast.success('Extraction completed', {
        id: toastId,
        description: `${result.transactions.length} transactions extracted.`,
      })
    } catch (error) {
      toast.error('Retry failed', { id: toastId, description: errorMessage(error) })
    } finally {
      setPending(false)
      await Promise.all([
        mutate(apiKeys.statement(statementId)),
        mutate(apiKeys.transactions(statementId)),
        mutate(apiKeys.statements),
      ])
      onSettled?.()
    }
  }

  return (
    <Button onClick={handleRetry} disabled={pending || props.disabled} {...props}>
      {pending ? <Loader2 className="animate-spin" aria-hidden="true" /> : <RotateCw aria-hidden="true" />}
      {pending ? 'Retrying…' : label}
    </Button>
  )
}
