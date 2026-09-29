"""Excel export for parsed bank-statement transactions.

Second deliverable in the incremental build order: takes the list of dicts
produced by ``statement_converter.parse_statement`` and writes a formatted
``.xlsx`` workbook. Database, backend, frontend, and Stripe work remain out
of scope for this step.
"""
from __future__ import annotations

from datetime import date
from typing import Any

from openpyxl import Workbook
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.worksheet.worksheet import Worksheet

HEADERS = ("Date", "Description", "Debit", "Credit", "Balance")

_HEADER_FONT = Font(bold=True, color="FFFFFF", name="Arial")
_HEADER_FILL = PatternFill(start_color="305496", end_color="305496", fill_type="solid")
_REVIEW_FILL = PatternFill(start_color="FFF2CC", end_color="FFF2CC", fill_type="solid")
_TOTAL_FONT = Font(bold=True, name="Arial")
_BODY_FONT = Font(name="Arial")
_MONEY_FORMAT = "#,##0.00"
# Pakistani-conventional day-first display (e.g. 31-Dec-2025), even though the
# underlying cell is a real Excel date value, not a string.
_DATE_FORMAT = "dd-mmm-yyyy"

# Column widths: generous for Description, sensible defaults elsewhere.
_COLUMN_WIDTHS = {"A": 14, "B": 48, "C": 16, "D": 16, "E": 16}


def export_to_excel(transactions: list[dict[str, Any]], output_path: str) -> None:
    """Write ``transactions`` to a formatted workbook at ``output_path``.

    Expects each dict to have ``date``, ``description``, ``debit``, ``credit``,
    ``balance``, and ``needs_review`` keys, matching the contract returned by
    ``parse_statement``. ``debit``/``credit``/``balance`` may be ``None``.
    """
    workbook = Workbook()
    sheet = workbook.active
    sheet.title = "Transactions"

    _write_header(sheet)

    row_index = 2
    for transaction in transactions:
        raw_date = transaction.get("date")
        date_value: date | str | None = date.fromisoformat(raw_date) if raw_date else raw_date
        date_cell = sheet.cell(row=row_index, column=1, value=date_value)
        date_cell.font = _BODY_FONT
        if isinstance(date_value, date):
            date_cell.number_format = _DATE_FORMAT
        sheet.cell(row=row_index, column=2, value=transaction.get("description")).font = _BODY_FONT

        for column, key in ((3, "debit"), (4, "credit"), (5, "balance")):
            cell = sheet.cell(row=row_index, column=column, value=transaction.get(key))
            cell.number_format = _MONEY_FORMAT
            cell.font = _BODY_FONT

        if transaction.get("needs_review"):
            for column in range(1, 6):
                sheet.cell(row=row_index, column=column).fill = _REVIEW_FILL

        row_index += 1

    last_data_row = row_index - 1
    _write_totals(sheet, row_index, last_data_row)

    sheet.freeze_panes = "A2"
    sheet.column_dimensions["B"].alignment = Alignment(wrap_text=False)
    for letter, width in _COLUMN_WIDTHS.items():
        sheet.column_dimensions[letter].width = width

    workbook.save(output_path)


def _write_header(sheet: Worksheet) -> None:
    for column, title in enumerate(HEADERS, start=1):
        cell = sheet.cell(row=1, column=column, value=title)
        cell.font = _HEADER_FONT
        cell.fill = _HEADER_FILL
        cell.alignment = Alignment(horizontal="left" if title == "Description" else "center")
    sheet.row_dimensions[1].height = 20


def _write_totals(sheet: Worksheet, totals_row: int, last_data_row: int) -> None:
    sheet.cell(row=totals_row, column=2, value="Totals").font = _TOTAL_FONT

    if last_data_row >= 2:
        debit_range = f"C2:C{last_data_row}"
        credit_range = f"D2:D{last_data_row}"
    else:
        # No transactions: SUM over an empty single-row range evaluates to 0
        # rather than erroring, so totals still render correctly.
        debit_range = "C2:C2"
        credit_range = "D2:D2"

    debit_cell = sheet.cell(row=totals_row, column=3, value=f"=SUM({debit_range})")
    credit_cell = sheet.cell(row=totals_row, column=4, value=f"=SUM({credit_range})")
    for cell in (debit_cell, credit_cell):
        cell.font = _TOTAL_FONT
        cell.number_format = _MONEY_FORMAT

    for column in range(1, 6):
        sheet.cell(row=totals_row, column=column).fill = PatternFill(
            start_color="D9D9D9", end_color="D9D9D9", fill_type="solid"
        )
