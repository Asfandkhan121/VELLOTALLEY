"""Basis questions and the recommendation rule (owner-approved wording, 2026-10-11).

A recommendation is only a suggestion: the bookkeeper confirms (PUT /basis) and nothing
here stores anything or touches needs_review / statements.confidence. Any "Not sure"
or any answer mix the rule does not cover gives no recommendation (stay unset).
"""
from __future__ import annotations

# signal values: cash_or_modified, accrual, cash, accrual_or_modified, none
QUESTIONS: list[dict] = [
    {"id": "income", "text": "How does the client record their regular income, sales, or funding?",
     "why": "Distinguishes whether income is driven by the physical receipt of money or by the act of earning it.",
     "options": [
         {"id": "cash", "label": "When the money actually hits the bank account.", "signal": "cash_or_modified"},
         {"id": "accrual", "label": "When the work is done, goods are delivered, or the invoice is sent, even if unpaid.", "signal": "accrual"},
         {"id": "unsure", "label": "Not sure.", "signal": "none"}]},
    {"id": "expenses", "text": "How are normal, day-to-day bills and operating costs recorded?",
     "why": "Clarifies if a payment clears a previously recorded liability, or if the payment itself is the expense.",
     "options": [
         {"id": "cash", "label": "As an expense only when the payment leaves the bank account.", "signal": "cash_or_modified"},
         {"id": "accrual", "label": "As an expense the moment the bill is received, even before it is paid.", "signal": "accrual"},
         {"id": "unsure", "label": "Not sure.", "signal": "none"}]},
    {"id": "assets_loans", "text": "How does the client track large equipment purchases, vehicles, or bank loans?",
     "why": "Separates strict cash-basis clients from those who track large balance-sheet items but keep daily operations on cash.",
     "options": [
         {"id": "cash", "label": "Just like regular expenses or income: recorded fully when the cash moves in or out.", "signal": "cash"},
         {"id": "tracked", "label": "They are recorded as long-term assets or debts that stay on the books over time.", "signal": "accrual_or_modified"},
         {"id": "unsure", "label": "Not sure / Not applicable.", "signal": "none"}]},
    {"id": "payroll_liabilities", "text": "Does the client track unpaid obligations, like payroll taxes or social contributions, before they are actually paid?",
     "why": "Tests if the client applies accrual principles to significant legal liabilities while otherwise relying on cash movements.",
     "options": [
         {"id": "cash", "label": "No, they are only recorded as an expense when the actual payment is made.", "signal": "cash"},
         {"id": "tracked", "label": "Yes, they are recorded as an unpaid debt the moment they are calculated or incurred.", "signal": "accrual_or_modified"},
         {"id": "unsure", "label": "Not sure / Not applicable.", "signal": "none"}]},
]


class InvalidAnswers(ValueError):
    pass


def recommend(answers: dict[str, str]) -> dict:
    """answers: question id -> option id. Returns {"recommendation": basis|None, "reason": str}."""
    if set(answers) != {q["id"] for q in QUESTIONS}:
        raise InvalidAnswers("Answer all four questions.")
    sig = {}
    for q in QUESTIONS:
        match = [o for o in q["options"] if o["id"] == answers[q["id"]]]
        if not match:
            raise InvalidAnswers(f"Unknown answer for {q['id']}.")
        sig[q["id"]] = match[0]["signal"]
    if "none" in sig.values():
        return {"recommendation": None, "reason": "At least one answer was Not sure, so no recommendation. Pick the basis yourself."}
    if sig["income"] == "accrual" and sig["expenses"] == "accrual":
        return {"recommendation": "accrual", "reason": "Income and expenses are both recorded when earned or billed."}
    if sig["income"] == "cash_or_modified" and sig["expenses"] == "cash_or_modified":
        if sig["assets_loans"] == "cash" and sig["payroll_liabilities"] == "cash":
            return {"recommendation": "cash", "reason": "Everything is recorded when cash moves."}
        return {"recommendation": "modified_cash", "reason": "Day-to-day items are on cash, but large items or payroll liabilities are tracked over time."}
    return {"recommendation": None, "reason": "Income and expense answers point different ways, so no recommendation. Pick the basis yourself."}
