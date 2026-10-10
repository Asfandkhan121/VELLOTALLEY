'use client'

import useSWR from 'swr'
import { ApiError, apiKeys, fetcher } from '@/lib/api'
import type { AccountHead, Client, ClientHead, Statement, StatementNote, Transaction } from '@/lib/types'

const shouldRetry = (error: unknown) =>
  !(error instanceof ApiError) || (error.status >= 500 && error.status !== 503) || error.status === 0

const baseOptions = {
  revalidateOnFocus: false,
  shouldRetryOnError: shouldRetry,
  errorRetryCount: 2,
}

export function useClients() {
  return useSWR<Client[]>(apiKeys.clients, fetcher, baseOptions)
}

export function useAccountHeads() {
  return useSWR<AccountHead[]>(apiKeys.accountHeads, fetcher, baseOptions)
}

export function useStatements() {
  return useSWR<Statement[]>(apiKeys.statements, fetcher, baseOptions)
}

export function useStatement(id: string, options?: { poll?: boolean }) {
  return useSWR<Statement>(apiKeys.statement(id), fetcher, {
    ...baseOptions,
    refreshInterval: (latest) =>
      options?.poll !== false && latest?.status === 'processing' ? 2500 : 0,
  })
}

export function useTransactions(id: string, enabled: boolean) {
  return useSWR<Transaction[]>(enabled ? apiKeys.transactions(id) : null, fetcher, baseOptions)
}

export function useNotes(id: string) {
  return useSWR<StatementNote[]>(apiKeys.notes(id), fetcher, baseOptions)
}

export function useClientMap() {
  const { data } = useClients()
  return new Map((data ?? []).map((client) => [client.id, client.name]))
}

export function useClientHeads(clientId: string) {
  return useSWR<ClientHead[]>(apiKeys.clientHeads(clientId), fetcher, baseOptions)
}
