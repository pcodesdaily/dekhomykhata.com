import pandas as pd
import pytest

from mykhata_ml import insights
from mykhata_ml.config import load_config

CFG = load_config()["insights"]


def tx(date, narration, category, amount, type_="DEBIT"):
    return {"date": date, "narration": narration, "category": category, "amount": amount, "type": type_,
            "balance_ok": True}


@pytest.fixture(scope="module")
def statement() -> pd.DataFrame:
    rows = []
    for m, groceries, food, netflix in [(1, 5000, 3000, 649), (2, 5200, 3100, 649), (3, 4900, 2900, 649),
                                        (4, 9000, 1000, 799)]:
        d = f"2024-{m:02d}"
        rows += [tx(f"{d}-01", "NEFT CR-INFOSYS LIMITED-SALARY", "SALARY", 50000, "CREDIT"),
                 tx(f"{d}-02", "UPI/DR/1/RAMESH/rent", "RENT", 15000),
                 tx(f"{d}-05", "ME DC SI NETFLIX", "ENTERTAINMENT", netflix),
                 tx(f"{d}-07", "ACH D- ZERODHA SIP", "INVESTMENT", 5000),
                 tx(f"{d}-10", "UPI/DR/2/DMART", "GROCERIES", groceries),
                 tx(f"{d}-12", "UPI/DR/3/SWIGGY", "FOOD_DINING", food),
                 tx(f"{d}-15", "POS AMAZON", "SHOPPING", 1000 + 100 * m),
                 tx(f"{d}-20", "POS MYNTRA", "SHOPPING", 1500)]
    rows += [tx("2024-04-25", "POS CROMA", "SHOPPING", 40000),
             tx("2024-04-12", "UPI/DR/4/SWIGGY", "FOOD_DINING", 450),
             tx("2024-04-12", "UPI/DR/5/SWIGGY", "FOOD_DINING", 450),
             tx("2024-03-03", "BY CASH DEPOSIT", "SELF_TRANSFER", 20000, "CREDIT")]
    return pd.DataFrame(rows)


@pytest.fixture(scope="module")
def rep(statement):
    return insights.report(statement, CFG, budgets={"GROCERIES": 6000})


def test_totals_ignore_self_transfers(rep) -> None:
    assert rep["totals"]["money_in"] == rep["totals"]["income_identified"] == 200000
    assert rep["period"]["months"] == 4
    march = next(r for r in rep["monthly"] if r["month"] == "2024-03")
    assert march["income"] == 50000


def test_savings_rate_and_overspent_month(rep) -> None:
    april = next(r for r in rep["monthly"] if r["month"] == "2024-04")
    assert april["spending"] == pytest.approx(15000 + 799 + 9000 + 1000 + 900 + 1400 + 1500 + 40000)
    assert rep["totals"]["months_overspent"] == ["2024-04"]
    assert 0 < rep["totals"]["savings_rate"] < 1


def test_503020(rep) -> None:
    r = rep["rule_503020"]
    assert r["available"] and set(r["verdict"]) == {"needs", "wants", "savings"}


def test_over_and_under_vs_typical_and_budget(rep) -> None:
    flags = {(r["month"], r["category"], r["basis"]): r["status"] for r in rep["over_under"]}
    assert flags[("2024-04", "GROCERIES", "your typical month")] == "over"
    assert flags[("2024-04", "GROCERIES", "budget")] == "over"
    assert flags[("2024-04", "FOOD_DINING", "your typical month")] == "under"


def test_unusual_and_double_charge(rep) -> None:
    assert [u["amount"] for u in rep["unusual"]] == [40000]
    assert rep["double_charges"] == [{"date": "2024-04-12", "narration": "UPI/DR/4/SWIGGY", "amount": 450.0, "times": 2}]


def test_recurring_finds_rent_emi_style_payments_and_price_hike(rep) -> None:
    found = {r["category"]: r for r in rep["recurring"]}
    assert {"RENT", "ENTERTAINMENT", "INVESTMENT"} <= set(found)
    assert found["ENTERTAINMENT"]["price_change"] and found["ENTERTAINMENT"]["last_amount"] == 799
    assert not found["RENT"]["price_change"]


def test_savings_follow_money_not_labels(statement) -> None:
    unlabelled = statement.assign(category=statement["category"].where(statement["category"] != "SALARY", "OTHER"))
    r = insights.report(unlabelled, CFG)
    assert r["totals"]["income_identified"] == 0 and r["totals"]["money_in"] == 200000
    assert r["totals"]["months_overspent"] == ["2024-04"]


def test_no_money_in_is_reported_not_crashed(statement) -> None:
    r = insights.report(statement[statement["type"] == "DEBIT"], CFG)
    assert r["rule_503020"]["available"] is False and r["totals"]["savings_rate"] is None
