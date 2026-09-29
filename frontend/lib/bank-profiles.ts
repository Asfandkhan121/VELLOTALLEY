import type { BankProfileOption } from '@/lib/types'

/**
 * The backend exposes no endpoint listing its BANK_PROFILES, so the supported
 * profile keys are mirrored through the BANK_PROFILES env var (comma-separated,
 * e.g. "mcb,allied"). Only "Auto detect" is offered when it is unset, which the
 * backend always accepts.
 */
export function getBankProfiles(): BankProfileOption[] {
  const configured = (process.env.BANK_PROFILES ?? '')
    .split(',')
    .map((value) => value.trim().toLowerCase())
    .filter((value) => value && value !== 'auto')

  return [
    { value: 'auto', label: 'Auto detect' },
    ...Array.from(new Set(configured)).map((value) => ({ value, label: value.toUpperCase() })),
  ]
}
