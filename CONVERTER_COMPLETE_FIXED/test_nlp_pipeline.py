from nlp.models import Decision, Method
from nlp.normalizer import normalize
from nlp.pipeline import analyze_transaction, analyze_transactions
from nlp.models import TransactionInput
from nlp.rules import match_rule


def test_normalize_lowercases_and_collapses_whitespace():
    assert normalize("  METRO   Cash & Carry  ") == "metro cash & carry"


def test_normalize_collapses_repeated_separators():
    assert normalize("METRO--CASH//CARRY") == "metro-cash-carry"


def test_normalize_preserves_numbers_and_references():
    # Spec section 10: never strip dates, amounts, reference numbers.
    text = "MCB POS 000123 METRO CASH & CARRY LAHORE PK"
    normalized = normalize(text)
    assert "000123" in normalized
    assert "lahore" in normalized


def test_rule_matches_atm_withdrawal():
    label, confidence = match_rule(normalize("ATM WITHDRAWAL KARACHI"))
    assert label == "atm"
    assert confidence > 0.9


def test_rule_matches_salary_not_substring_false_positive():
    # "salary" should match; an unrelated merchant containing similar
    # substrings should not falsely trigger via word-boundary matching.
    assert match_rule(normalize("SALARY CREDIT SEPTEMBER")) == ("salary", 0.98)
    assert match_rule(normalize("SALARYMEN TRADING CO")) is None  # no word boundary


def test_rule_returns_none_for_unknown_merchant():
    assert match_rule(normalize("BUKHARI GENERAL STORE LAHORE")) is None


def test_pipeline_accepts_on_rule_match():
    result = analyze_transaction(TransactionInput(description="ATM WITHDRAWAL LHR"), candidates=[])
    assert result.decision == Decision.ACCEPT
    assert result.method == Method.RULE
    assert result.rule_label == "atm"
    # Original description must survive untouched (spec section 9).
    assert result.original_description == "ATM WITHDRAWAL LHR"


def test_pipeline_reviews_unknown_transaction_with_no_candidates():
    result = analyze_transaction(TransactionInput(description="BUKHARI GENERAL STORE"), candidates=[])
    assert result.decision == Decision.REVIEW
    assert result.method == Method.NONE
    assert result.review_reasons


def test_pipeline_accepts_on_strong_fuzzy_match():
    result = analyze_transaction(
        TransactionInput(description="METRO CASH & CARY LAHORE"),  # misspelled "CARY"
        candidates=["metro cash & carry lahore"],
    )
    assert result.decision == Decision.ACCEPT
    assert result.method == Method.FUZZY_MATCH
    assert result.fuzzy_similarity is not None and result.fuzzy_similarity >= 92.0


def test_pipeline_reviews_on_weak_fuzzy_match():
    result = analyze_transaction(
        TransactionInput(description="ABC TRADERS"),
        candidates=["xyz distributors"],
    )
    assert result.decision == Decision.REVIEW


def test_batch_recognizes_repeated_merchant_within_statement():
    items = [
        TransactionInput(description="METRO CASH & CARRY LAHORE"),
        TransactionInput(description="METRO CASH & CARY LAHORE"),  # repeat, slight misspelling
    ]
    results = analyze_transactions(items)
    # First occurrence has no candidates yet, so it can't fuzzy-accept
    # against something not yet seen -- correctly falls to REVIEW.
    assert results[0].decision == Decision.REVIEW
    # Second occurrence should now match the first via fuzzy matching.
    assert results[1].decision == Decision.ACCEPT
    assert results[1].method == Method.FUZZY_MATCH


def test_no_fake_method_labels():
    # Spec section 33: never claim a tier ran that didn't. A REVIEW
    # result with no rule/fuzzy match must report method=NONE, never a
    # tier that isn't implemented.
    result = analyze_transaction(TransactionInput(description="UNRECOGNIZABLE XYZ 999"), candidates=[])
    assert result.method == Method.NONE
    assert result.classifier_label is None
    assert result.semantic_similarity is None
