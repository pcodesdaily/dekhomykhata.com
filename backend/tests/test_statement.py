from pathlib import Path

import pandas as pd
import pytest

from mykhata_ml import data, statement
from mykhata_ml.config import path

SAMPLES = sorted(path("data/raw/statements").glob("*/00001.pdf"))


@pytest.mark.parametrize("cell,signed,expected", [
    ("Rs. 6,086.63", False, 6086.63), ("1,011,783.23", False, 1011783.23), ("₹ 500", False, 500.0),
    ("Rs. -3,919.51", True, -3919.51), ("3,919.51 Dr", True, -3919.51), ("1,234.00 Cr", True, 1234.0),
    ("", False, None), ("-", False, None),
])
def test_parse_amount(cell, signed, expected) -> None:
    assert statement.parse_amount(cell, signed=signed) == expected


@pytest.mark.parametrize("cell", ["01-01-2024\n11:30:55", "01/01/2024", "01 Jan 2024", "01-Jan-24", "2024-01-01"])
def test_parse_date(cell) -> None:
    assert statement.parse_date(cell) == pd.Timestamp("2024-01-01")


def test_header_map_needs_money_columns() -> None:
    assert statement._header_map(["Txn Date", "Description", "Debit", "Credit", "Balance"]) is not None
    assert statement._header_map(["Date", "Narration", "Amount", "Cr/Dr", "Available Balance"]) is not None
    assert statement._header_map(["Account Holder", "RAHUL SHARMA"]) is None


@pytest.mark.parametrize("pdf", SAMPLES, ids=lambda p: p.parent.name)
def test_parse_matches_ground_truth(pdf: Path) -> None:
    parsed, truth = statement.parse(pdf), data.load_statement_truth(pdf.with_suffix(".json"))
    assert len(parsed) == len(truth)
    assert (parsed["date"] == truth["date"]).all()
    assert ((parsed["amount"] - truth["amount"]).abs() < 0.005).all()
    assert (parsed["type"] == truth["type"]).all()
    assert (parsed["narration"].str.replace(" ", "") == truth["narration"].str.replace(" ", "")).all()


def test_balance_check_flags_broken_rows() -> None:
    df = pd.DataFrame({"type": ["CREDIT", "DEBIT", "DEBIT"], "amount": [100.0, 30.0, 10.0],
                       "balance": [100.0, 70.0, 50.0]})
    assert statement.balance_check(df).tolist() == [True, True, False]


def test_rejects_non_pdf(tmp_path) -> None:
    fake = tmp_path / "statement.pdf"
    fake.write_text("hello")
    with pytest.raises(statement.StatementError, match="not a PDF"):
        statement.parse(fake)
