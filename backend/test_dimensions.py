from datetime import date

from nlp.dimensions import discover_dimensions


def _campus_rows():
    out = []
    for n in range(1, 7):
        for m in range(1, 4):  # each campus recurs, in different months
            out += [(f"Security Guard Payment Campus-{n}", date(2025, m, 5)),
                    (f"Campus {n} contribution", date(2025, m, 9))]
    return out


def test_finds_recurring_branch_whatever_the_word_is():
    rows = _campus_rows()
    dims = discover_dimensions([r[0] for r in rows], [r[1] for r in rows])
    assert len(dims) == 1
    assert set(dims[0].values) == {"1", "2", "3", "4", "5", "6"}
    # same logic with a different word and a name-style value, nothing hard-coded
    rows2 = [(f"Rent from {b} outlet", date(2025, 1, 1)) for b in ["alpha", "beta", "gamma"] * 3]
    assert {*discover_dimensions([r[0] for r in rows2])[0].values} == {"alpha", "beta", "gamma"}


def test_alias_spellings_merge_into_one_dimension():
    narr = [f"Loan to campus {n} for fees" for n in range(1, 5) for _ in range(2)]
    narr += [f"Student refund c {n} fees" for n in range(1, 5) for _ in range(2)]
    narr += [f"Loan to c {n} for fees" for n in range(1, 5)]
    dims = discover_dimensions(narr)
    assert len(dims) == 1 and set(dims[0].values) == {"1", "2", "3", "4"}


def test_single_unit_book_creates_no_dimension():
    narr = ["Bank charges", "Salary for staff", "Utility bill paid", "Office supplies", "Salary for staff"] * 4
    assert discover_dimensions(narr) == []


def test_cheque_numbers_and_ids_are_not_dimensions():
    narr = [f"Ch {10350100 + i} security refund" for i in range(30)]
    assert discover_dimensions(narr) == []


def test_months_are_periods_not_branches():
    months = ["jan", "feb", "mar", "apr"]
    rows = [(f"EOBI M/O {m} 25", date(2025, i + 1, 3)) for i, m in enumerate(months) for _ in range(3)]
    assert discover_dimensions([r[0] for r in rows]) != []            # looks like a slot without dates
    assert discover_dimensions([r[0] for r in rows], [r[1] for r in rows]) == []  # dropped with dates
