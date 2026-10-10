export type StatementStatus = 'processing' | 'completed' | 'failed'
export type ExtractionMethod = 'profile' | 'heuristic' | 'llm'

export interface AccountHead {
  id: string
  main_head: string
  sub_head: string
}

export interface Client {
  id: string
  name: string
  created_at: string
}

export interface Statement {
  id: string
  client_id: string
  original_filename: string
  bank_profile: string
  uploaded_at: string
  status: StatementStatus
  extraction_method: ExtractionMethod | null
  confidence: number | string | null
  /** Optional extraction metadata surfaced by the backend when available. */
  layout_detected?: string | null
  date_format_ambiguous?: boolean
}

export interface Transaction {
  date: string | null
  description: string | null
  debit: string | number | null
  credit: string | number | null
  balance: string | number | null
  needs_review: boolean
  nlp_insight?: NlpInsight | null
}

export interface NlpInsight {
  decision: 'accept' | 'review'
  method: 'rule' | 'fuzzy_match' | 'classifier' | 'semantic_match' | 'none'
  normalized_description: string
  rule_label: string | null
  rule_confidence: number | null
  fuzzy_match_text: string | null
  fuzzy_similarity: number | null
  review_reasons: string[]
}

export interface ExtractionResult {
  statement_id: string
  transactions: Transaction[]
  extraction_method: ExtractionMethod
  confidence?: number | null
  layout_detected?: string | null
  date_format_ambiguous?: boolean
}

export interface StatementNote {
  id: string
  note: string
  created_at: string
}

export interface BankProfileOption {
  value: string
  label: string
}

export interface ClientHead {
  id: string
  name: string
  section: string | null
  code: string | null
  source: 'trial_balance' | 'cash_book' | 'manual'
  confirmed_at: string | null
}

export interface HeadProposal {
  name: string
  section: string | null
  code: string | null
  row: number
}

export interface HeadProposalSheet {
  sheet: string
  entity: string | null
  period: string | null
  stated_basis: string | null
  hierarchy: boolean
  warnings: string[]
  evidence: Record<string, string[]>
  heads: HeadProposal[]
}

export interface ConfirmHeadsResult {
  created: number
  skipped_existing: string[]
}
