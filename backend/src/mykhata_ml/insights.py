"""Spending insights from categorised transactions: cash flow, savings, 50/30/20, over/under spend,
unusual amounts, possible double charges and recurring payments."""

from typing import Any

import numpy as np
import pandas as pd

from mykhata_ml.categories import CATEGORIES
from mykhata_ml.data import normalize

SPEND_BUCKETS = ["need", "want", "debt", "cash", "unknown"]


def _prepare(tx: pd.DataFrame) -> pd.DataFrame:
    tx = tx.copy()
    tx["date"] = pd.to_datetime(tx["date"])
    tx["month"] = tx["date"].dt.to_period("M").astype(str)
    tx["bucket"] = tx["category"].map(lambda c: CATEGORIES[c]["bucket"])
    tx["key"] = tx["narration"].map(normalize)
    tx["is_debit"] = tx["type"] == "DEBIT"
    return tx


def monthly(tx: pd.DataFrame) -> pd.DataFrame:
    real = tx[tx["category"] != "SELF_TRANSFER"]
    debit, credit = real[real["is_debit"]], real[~real["is_debit"]]
    pivot = lambda df: df.pivot_table(index="month", columns="bucket", values="amount", aggfunc="sum")
    spend, got = pivot(debit), pivot(credit)
    out = pd.DataFrame(index=sorted(tx["month"].unique()))
    for b in SPEND_BUCKETS + ["saving"]:
        out[b] = spend.get(b)
    out["transfers_out"] = spend.get("transfer")
    refund = credit["category"] == "REFUND_CASHBACK"
    out["income"] = credit[~refund & (credit["bucket"] == "income")].groupby("month")["amount"].sum()
    out["refunds"] = credit[refund].groupby("month")["amount"].sum()
    out["transfers_in"] = got.get("transfer")
    out["other_in"] = got.get("unknown")
    out = out.fillna(0.0)
    out["spending"] = out[SPEND_BUCKETS].sum(axis=1) - out["refunds"]
    out["money_in"] = credit.groupby("month")["amount"].sum().reindex(out.index, fill_value=0) - out["refunds"]
    out["net_flow"] = credit.groupby("month")["amount"].sum().reindex(out.index, fill_value=0)         - debit.groupby("month")["amount"].sum().reindex(out.index, fill_value=0)
    out["savings"] = out["net_flow"] + out["saving"].fillna(0)
    out["savings_rate"] = out["savings"] / out["money_in"].where(out["money_in"] > 0)
    return out.rename(columns={"need": "needs", "want": "wants", "saving": "invested", "unknown": "unallocated"})


def rule_503020(m: pd.DataFrame, rule: dict[str, float]) -> dict[str, Any]:
    income = m["money_in"].sum()
    if income <= 0:
        return {"available": False, "reason": "no money came into this account"}
    shares = {"needs": (m["needs"].sum() + m["debt"].sum()) / income, "wants": m["wants"].sum() / income,
              "savings": m["savings"].sum() / income}
    verdict = {"needs": "over" if shares["needs"] > rule["needs"] else "ok",
               "wants": "over" if shares["wants"] > rule["wants"] else "ok",
               "savings": "under" if shares["savings"] < rule["savings"] else "ok"}
    return {"available": True, "shares": shares, "target": rule, "verdict": verdict,
            "unallocated_share": (m["cash"].sum() + m["unallocated"].sum()) / income,
            "income_identified_share": m["income"].sum() / income}


def over_under(tx: pd.DataFrame, cfg: dict[str, Any], budgets: dict[str, float] | None = None) -> list[dict]:
    spend = tx[tx["is_debit"] & tx["bucket"].isin(["need", "want"])]
    table = spend.pivot_table(index="month", columns="category", values="amount", aggfunc="sum").fillna(0.0)
    rows = []
    for i, month in enumerate(table.index):
        history = table.iloc[:i]
        for cat in table.columns:
            amount = float(table.at[month, cat])
            if budgets and cat in budgets and abs(amount - budgets[cat]) >= cfg["min_delta"]:
                rows.append({"month": month, "category": cat, "amount": amount, "reference": budgets[cat],
                             "basis": "budget", "status": "over" if amount > budgets[cat] else "under"})
            if len(history) < cfg["min_history_months"]:
                continue
            typical = float(history[cat].median())
            if typical <= 0 or abs(amount - typical) < cfg["min_delta"]:
                continue
            ratio = amount / typical
            if ratio >= cfg["over_ratio"] or ratio <= cfg["under_ratio"]:
                rows.append({"month": month, "category": cat, "amount": amount, "reference": typical,
                             "basis": "your typical month", "status": "over" if ratio > 1 else "under"})
    return rows


def unusual(tx: pd.DataFrame, cfg: dict[str, Any]) -> list[dict]:
    debit = tx[tx["is_debit"] & (tx["category"] != "SELF_TRANSFER")]
    rows = []
    for cat, g in debit.groupby("category"):
        if len(g) < cfg["min_rows"]:
            continue
        log = np.log(g["amount"])
        mad = (log - log.median()).abs().median()
        if mad == 0:
            continue
        z = 0.6745 * (log - log.median()) / mad
        for i in g.index[(z > cfg["z"]) & (g["amount"] >= cfg["min_amount"])]:
            rows.append({"date": str(g.at[i, "date"].date()), "narration": g.at[i, "narration"], "category": cat,
                         "amount": float(g.at[i, "amount"]), "typical": float(g["amount"].median())})
    return rows


def double_charges(tx: pd.DataFrame) -> list[dict]:
    debit = tx[tx["is_debit"] & (tx["category"] != "OTHER")]
    dup = debit[debit.duplicated(["date", "key", "amount"], keep=False)]
    return [{"date": str(d.date()), "narration": g["narration"].iloc[0], "amount": float(a), "times": len(g)}
            for (d, _, a), g in dup.groupby(["date", "key", "amount"])]


def recurring(tx: pd.DataFrame, cfg: dict[str, Any]) -> list[dict]:
    debit = tx[tx["is_debit"] & ~tx["category"].isin(["OTHER", "TRANSFER_OUT", "SELF_TRANSFER", "CASH_WITHDRAWAL"])]
    rows = []
    for (key, cat), g in debit.groupby(["key", "category"]):
        months = g["month"].nunique()
        amounts = g.sort_values("date")["amount"]
        if months < cfg["min_months"] or amounts.std(ddof=0) / amounts.mean() > cfg["max_amount_cv"]:
            continue
        typical = float(amounts.iloc[:-1].median())
        change = abs(amounts.iloc[-1] - typical)
        rows.append({"narration": g["narration"].iloc[-1], "category": cat, "months": int(months),
                     "typical_amount": typical, "last_amount": float(amounts.iloc[-1]),
                     "price_change": bool(change / typical > cfg["price_change"] and change >= cfg["min_change"])})
    return sorted(rows, key=lambda r: -r["typical_amount"])


def report(tx: pd.DataFrame, cfg: dict[str, Any], budgets: dict[str, float] | None = None) -> dict[str, Any]:
    tx = _prepare(tx)
    m = monthly(tx)
    money_in, savings = m["money_in"].sum(), m["savings"].sum()
    return {
        "period": {"from": str(tx["date"].min().date()), "to": str(tx["date"].max().date()), "months": len(m)},
        "totals": {"money_in": money_in, "income_identified": m["income"].sum(), "spending": m["spending"].sum(),
                   "invested": m["invested"].sum(), "savings": savings,
                   "savings_rate": savings / money_in if money_in > 0 else None,
                   "months_overspent": m.index[m["savings"] < 0].tolist()},
        "spending_by_category": tx[tx["is_debit"] & tx["bucket"].isin(["need", "want", "debt"])]
            .groupby("category")["amount"].sum().sort_values(ascending=False).to_dict(),
        "monthly": m.reset_index(names="month").to_dict(orient="records"),
        "rule_503020": rule_503020(m, cfg["rule"]),
        "over_under": over_under(tx, cfg["over_under"], budgets),
        "unusual": unusual(tx, cfg["unusual"]),
        "double_charges": double_charges(tx),
        "recurring": recurring(tx, cfg["recurring"]),
        "data_quality": {"transactions": len(tx), "uncategorised_share": float((tx["category"] == "OTHER").mean()),
                         "balance_check_failures": int((~tx["balance_ok"]).sum()) if "balance_ok" in tx else None},
    }
