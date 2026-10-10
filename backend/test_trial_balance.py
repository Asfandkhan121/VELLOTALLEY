import io

from openpyxl import Workbook

from trial_balance import basis_evidence, parse_rows, read_workbook


def zoho():
    return [
        ["Acme Trading LLC\nTrial Balance\nBasis: Accrual\nFrom 01 Jan 2025 To 31 Dec 2025"],
        ["Account ", "Account Code ", "Net Debit ", "Net Credit ", "Opening Balance ", "Closing Balance "],
        [],
        ["Assets", "", ""],
        ["          Accounts Receivable", "", 100, 0, 50, 150],
        ["          Prepaid Expenses", "", 10, 0, 0, 10],
        ["Liabilities", "", ""],
        ["          Accrued Salaries", "", 0, 30, 0, -30],
        ["Income", "", ""],
        ["          Consulting Income", "", 0, 500, 0, -500],
        ["Total", "", 110, 530, 0, 0],
    ]


def tally():
    return [
        ["NOVUS FZE"], ["Trial Balance"], ["1-Jan-25 to 31-Dec-25"],
        ["Particulars", "1-Jan-25 to 31-Dec-25"],
        ["", "Opening", "Transactions", "", "Closing"],
        ["", "Balance", "Debit", "Credit", "Balance"],
        ["Fixed Assets", 3215, None, None, 3215],
        ["Laptop", 2255, None, None, 2255],
        ["Sundry Debtors", 846697.55, 9493261.45, 9435160.74, 904798.26],
        ["Sales Accounts", None, 389181.18, 7434540.27, 7045359.09],
    ]


def coded():
    return [
        ["Trial Balance\nBono Concepts DMCC"], ["As at 30 September 2025"],
        ["ACCOUNT CODE", "ACCOUNT", "ACCOUNT TYPE", "DEBIT - YEAR TO DATE", "CREDIT - YEAR TO DATE"],
        [3100, "Services rendered\n(Overseas)", "Revenue", None, 97380.01],
        [5010, "Office rental", "Expense", 16625, "-"],
    ]


def two_years():
    return [["Beinit Energy"], ["Trial balance"], [None, None, 2024, None, None, None, 2023],
            ["Particulars", None, "Debit", "Credit", None, None, "Debit", "Credit"],
            ["Laptop", None, 6857, None, None, None, 5000, None],
            ["Cash at banks", None, 7024, None, None, None, 100, None]]


def test_zoho_sections_stated_basis_and_totals_skipped():
    tb = parse_rows("s", zoho())
    assert tb.stated_basis == "accrual" and tb.entity == "Acme Trading LLC"
    assert [a.name for a in tb.accounts] == ["Accounts Receivable", "Prepaid Expenses", "Accrued Salaries", "Consulting Income"]
    assert [a.section for a in tb.accounts] == ["Assets", "Assets", "Liabilities", "Income"]
    assert tb.hierarchy == "sections" and tb.accounts[0].values["Closing Balance"] == 150


def test_tally_two_row_header_and_unknown_group_structure_is_flagged():
    tb = parse_rows("s", tally())
    assert tb.name_column == 0 and tb.stated_basis is None
    assert "Closing Balance" in tb.amount_columns.values()
    assert [a.name for a in tb.accounts] == ["Fixed Assets", "Laptop", "Sundry Debtors", "Sales Accounts"]
    assert tb.hierarchy == "unknown" and any("group structure" in w for w in tb.warnings)


def test_coded_chart_uses_type_column_and_dash_is_zero():
    tb = parse_rows("s", coded())
    assert [a.name for a in tb.accounts] == ["Services rendered (Overseas)", "Office rental"]
    assert [a.section for a in tb.accounts] == ["Revenue", "Expense"]
    assert tb.accounts[0].code == "3100" and tb.hierarchy == "type_column"
    assert tb.accounts[1].values["CREDIT - YEAR TO DATE"] == 0.0


def test_repeated_headers_keep_both_years():
    tb = parse_rows("s", two_years())
    assert len(set(tb.amount_columns.values())) == len(tb.amount_columns) == 4
    assert sorted(tb.accounts[0].values.values()) == [5000.0, 6857.0]


def test_evidence_lists_matching_ledgers_not_a_decision():
    ev = basis_evidence(parse_rows("s", zoho()).accounts)
    assert ev == {"receivables": ["Accounts Receivable"], "prepayments": ["Prepaid Expenses"], "accruals": ["Accrued Salaries"]}
    assert basis_evidence(parse_rows("s", coded()).accounts) == {}


def test_unreadable_sheets_warn_instead_of_crashing():
    assert parse_rows("s", []).warnings
    assert "header" in parse_rows("s", [["just", "some"], ["random", 1]]).warnings[0]


def test_read_workbook_skips_hidden_sheets():
    wb = Workbook()
    ws = wb.active
    ws.title = "visible"
    for r in zoho():
        ws.append(r)
    wb.create_sheet("hidden").sheet_state = "hidden"
    buf = io.BytesIO()
    wb.save(buf)
    out = read_workbook(buf.getvalue())
    assert [t.sheet for t in out] == ["visible"] and len(out[0].accounts) == 4
