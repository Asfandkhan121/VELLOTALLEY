"""
Self-hosted transaction-intelligence layer for Vellotalley.

This is a SEPARATE concept from the existing statement-level extraction
confidence (`statements.confidence`, set by the profile/heuristic/LLM
parser tiers). That answers "was the PDF read correctly?" This module
analyzes transaction wording as a separate signal; its decision never
suppresses human review or changes the parser's extraction fields.

The extraction and transaction-preview endpoints expose these results as
separate text-only insights. They never change parser confidence or the
unconditional `needs_review` flag.

No paid or hosted external API is called anywhere in this package. Every
model referenced runs locally. As of this module's first version, only
the deterministic tiers (normalization, rules, fuzzy matching) are
implemented -- the classifier, semantic-similarity, and entity-extraction
tiers are deliberately not yet built (see pipeline.py for exactly what
exists today vs. what's stubbed).
"""
from .pipeline import analyze_transaction, analyze_transactions
from .models import TransactionInput, TransactionAnalysis, Decision

__all__ = [
    "analyze_transaction",
    "analyze_transactions",
    "TransactionInput",
    "TransactionAnalysis",
    "Decision",
]
