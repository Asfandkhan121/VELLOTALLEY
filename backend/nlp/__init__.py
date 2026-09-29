"""
Self-hosted transaction-intelligence layer for Ledgerly/Vellotalley.

This is a SEPARATE concept from the existing statement-level extraction
confidence (`statements.confidence`, set by the profile/heuristic/LLM
parser tiers). That answers "was the PDF read correctly?" This module
answers a different question per transaction: "do we understand what
this transaction is, well enough to skip human review?"

Nothing in this package is wired into the extraction endpoint yet. It is
built and tested standalone first, per this project's incremental-build
rule, and connected to the real pipeline as an explicit next step once
this piece is reviewed.

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
