'use client'

import { useRef, useState } from 'react'
import { useRouter } from 'next/navigation'
import { FileText, Loader2, Plus, Upload, X } from 'lucide-react'
import { toast } from 'sonner'
import { useSWRConfig } from 'swr'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Label } from '@/components/ui/label'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import { AddClientDialog } from '@/components/app/add-client-dialog'
import { apiKeys, createStatement, errorMessage, extractStatement } from '@/lib/api'
import { formatFileSize } from '@/lib/format'
import { useClients } from '@/lib/hooks'
import { cn } from '@/lib/utils'
import type { BankProfileOption, Client } from '@/lib/types'

function StepLabel({ index, title }: { index: number; title: string }) {
  return (
    <div className="flex items-center gap-2">
      <span className="flex size-6 shrink-0 items-center justify-center rounded-full bg-accent text-xs font-semibold text-accent-foreground">
        {index}
      </span>
      <span className="text-sm font-medium">{title}</span>
    </div>
  )
}

export function NewConversionForm({ bankProfiles }: { bankProfiles: BankProfileOption[] }) {
  const router = useRouter()
  const { mutate } = useSWRConfig()
  const { data: clients, isLoading: clientsLoading } = useClients()
  const fileInputRef = useRef<HTMLInputElement>(null)

  const [clientId, setClientId] = useState<string>('')
  const [bankProfile, setBankProfile] = useState<string>('auto')
  const [file, setFile] = useState<File | null>(null)
  const [fileError, setFileError] = useState<string | null>(null)
  const [formError, setFormError] = useState<string | null>(null)
  const [phase, setPhase] = useState<'idle' | 'creating' | 'extracting'>('idle')

  const submitting = phase !== 'idle'
  const hasClients = (clients?.length ?? 0) > 0

  function selectFile(picked: File | undefined) {
    setFileError(null)
    if (!picked) return
    const isPdf =
      picked.type === 'application/pdf' || picked.name.toLowerCase().endsWith('.pdf')
    if (!isPdf) {
      setFile(null)
      setFileError('Only PDF files are supported. Please choose a .pdf statement.')
      return
    }
    setFile(picked)
  }

  function clearFile() {
    setFile(null)
    setFileError(null)
    if (fileInputRef.current) fileInputRef.current.value = ''
  }

  async function handleSubmit(event: React.FormEvent) {
    event.preventDefault()
    setFormError(null)

    if (!clientId) {
      setFormError('Select a client before converting.')
      return
    }
    if (!file) {
      setFileError('Choose a PDF statement to convert.')
      return
    }

    setPhase('creating')
    try {
      const statement = await createStatement({ clientId, bankProfile, file })
      setPhase('extracting')
      // Extraction can take time; kick it off, then hand off to the detail
      // page, which polls while the statement is processing.
      extractStatement(statement.id).catch(() => {
        // Extraction failures surface as a failed status on the detail page,
        // where the user can retry.
      })
      await mutate(apiKeys.statements)
      toast.success('Statement uploaded', { description: 'Extraction is now in progress.' })
      router.push(`/statements/${statement.id}`)
    } catch (error) {
      setFormError(errorMessage(error))
      setPhase('idle')
    }
  }

  function onClientCreated(client: Client) {
    setClientId(client.id)
  }

  return (
    <form onSubmit={handleSubmit} className="flex flex-col gap-6">
      {/* Step 1 — Client */}
      <Card>
        <CardHeader>
          <CardTitle>
            <StepLabel index={1} title="Select client" />
          </CardTitle>
          <CardDescription>Choose which client this statement belongs to.</CardDescription>
        </CardHeader>
        <CardContent>
          {clientsLoading ? (
            <div className="h-8 w-full max-w-sm animate-pulse rounded-lg bg-muted" />
          ) : hasClients ? (
            <div className="flex flex-col gap-2">
              <Label htmlFor="client-select" className="sr-only">
                Client
              </Label>
              <div className="flex flex-wrap items-center gap-2">
                <Select value={clientId} onValueChange={(value) => setClientId(String(value))}>
                  <SelectTrigger id="client-select" className="w-full max-w-sm" disabled={submitting}>
                    <SelectValue placeholder="Select a client" />
                  </SelectTrigger>
                  <SelectContent>
                    {(clients ?? []).map((client) => (
                      <SelectItem key={client.id} value={client.id}>
                        {client.name}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
                <AddClientDialog
                  trigger={
                    <Button type="button" variant="outline" disabled={submitting}>
                      <Plus aria-hidden="true" />
                      Add client
                    </Button>
                  }
                  onCreated={onClientCreated}
                />
              </div>
            </div>
          ) : (
            <div className="flex flex-col items-start gap-3 rounded-lg border border-dashed p-4">
              <div>
                <p className="text-sm font-medium">No clients yet</p>
                <p className="text-sm text-muted-foreground">
                  Add a client to organize this statement before converting.
                </p>
              </div>
              <AddClientDialog
                trigger={
                  <Button type="button">
                    <Plus aria-hidden="true" />
                    Add client
                  </Button>
                }
                onCreated={onClientCreated}
              />
            </div>
          )}
        </CardContent>
      </Card>

      {/* Step 2 — Bank profile */}
      <Card>
        <CardHeader>
          <CardTitle>
            <StepLabel index={2} title="Select bank profile" />
          </CardTitle>
          <CardDescription>
            Known bank layouts can use a dedicated profile for higher accuracy. Auto detect handles
            any other layout.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <Label htmlFor="bank-select" className="sr-only">
            Bank profile
          </Label>
          <Select value={bankProfile} onValueChange={(value) => setBankProfile(String(value))}>
            <SelectTrigger id="bank-select" className="w-full max-w-sm" disabled={submitting}>
              <SelectValue placeholder="Auto detect" />
            </SelectTrigger>
            <SelectContent>
              {bankProfiles.map((profile) => (
                <SelectItem key={profile.value} value={profile.value}>
                  {profile.label}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </CardContent>
      </Card>

      {/* Step 3 — Upload */}
      <Card>
        <CardHeader>
          <CardTitle>
            <StepLabel index={3} title="Upload PDF" />
          </CardTitle>
          <CardDescription>Select the bank statement PDF you want to convert.</CardDescription>
        </CardHeader>
        <CardContent>
          <input
            ref={fileInputRef}
            id="statement-file"
            type="file"
            accept="application/pdf,.pdf"
            className="sr-only"
            disabled={submitting}
            onChange={(event) => selectFile(event.target.files?.[0])}
          />
          {file ? (
            <div className="flex items-center gap-3 rounded-lg border p-3">
              <span className="flex size-9 shrink-0 items-center justify-center rounded-lg bg-accent text-accent-foreground">
                <FileText className="size-4.5" aria-hidden="true" />
              </span>
              <div className="min-w-0 flex-1">
                <p className="truncate text-sm font-medium" title={file.name}>
                  {file.name}
                </p>
                <p className="text-xs text-muted-foreground">{formatFileSize(file.size)}</p>
              </div>
              <div className="flex items-center gap-1">
                <Button
                  type="button"
                  variant="outline"
                  size="sm"
                  disabled={submitting}
                  onClick={() => fileInputRef.current?.click()}
                >
                  Replace
                </Button>
                <Button
                  type="button"
                  variant="ghost"
                  size="icon-sm"
                  aria-label="Remove selected file"
                  disabled={submitting}
                  onClick={clearFile}
                >
                  <X aria-hidden="true" />
                </Button>
              </div>
            </div>
          ) : (
            <Label
              htmlFor="statement-file"
              className={cn(
                'flex cursor-pointer flex-col items-center justify-center gap-2 rounded-lg border border-dashed px-6 py-10 text-center transition-colors hover:border-foreground/30 hover:bg-muted/40',
                fileError && 'border-destructive/50',
                submitting && 'pointer-events-none opacity-60',
              )}
            >
              <span className="flex size-10 items-center justify-center rounded-full bg-accent text-accent-foreground">
                <Upload className="size-5" aria-hidden="true" />
              </span>
              <span className="text-sm font-medium">Choose a PDF statement</span>
              <span className="text-xs text-muted-foreground">PDF files only</span>
            </Label>
          )}
          {fileError ? (
            <p role="alert" className="mt-2 text-sm text-destructive">
              {fileError}
            </p>
          ) : null}
        </CardContent>
      </Card>

      {/* Step 4 — Convert */}
      {formError ? (
        <div
          role="alert"
          className="rounded-lg border border-destructive/30 bg-destructive/5 px-4 py-3 text-sm text-destructive"
        >
          {formError}
        </div>
      ) : null}

      <div className="flex flex-col items-stretch gap-3 sm:flex-row sm:items-center sm:justify-between">
        <p className="text-xs text-muted-foreground">
          Free plan includes 3 conversions per month.
        </p>
        <Button type="submit" size="lg" disabled={submitting || !hasClients}>
          {submitting ? <Loader2 className="animate-spin" aria-hidden="true" /> : null}
          {phase === 'creating'
            ? 'Uploading…'
            : phase === 'extracting'
              ? 'Starting extraction…'
              : 'Convert statement'}
        </Button>
      </div>
    </form>
  )
}
