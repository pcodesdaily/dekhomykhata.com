"""Synthetic data generation, text normalisation and merchant-grouped splits."""

import json
import math
import re
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from sklearn.model_selection import StratifiedGroupKFold, train_test_split

from mykhata_ml.config import path
from mykhata_ml.synth import NarrationGenerator

_DIGITS = re.compile(r"\d+")
_SPACES = re.compile(r"\s+")
_TYPE_TOKEN = {"DEBIT": "txdebit", "CREDIT": "txcredit"}


def normalize(narration) -> str:
    text = "" if pd.isna(narration) else str(narration)
    return _SPACES.sub(" ", _DIGITS.sub("0", text.lower())).strip()


def amount_token(amount) -> str:
    return f"amt{int(math.log2(max(float(amount), 1)))}"


def model_text(narrations, types, amounts) -> list[str]:
    return [f"{_TYPE_TOKEN.get(str(t).upper(), '')} {amount_token(a)} {normalize(n)}"
            for n, t, a in zip(narrations, types, amounts)]


def texts(df: pd.DataFrame) -> list[str]:
    return model_text(df["narration"], df["type"], df["amount"])


def generate(cfg: dict[str, Any]) -> pd.DataFrame:
    d = cfg["data"]
    gen = NarrationGenerator(seed=cfg["seed"], popularity=d["brand_popularity"])
    return pd.DataFrame(gen.generate(d["synthetic_rows"], sampling=d["sampling"]))


def clean(df: pd.DataFrame, majority: float = 0.9, z_max: float = 3.5) -> tuple[pd.DataFrame, dict[str, int]]:
    """Drop empty/invalid rows, relabel ambiguous texts as OTHER, drop amount outliers and duplicates."""
    stats = {"raw_rows": len(df)}
    df = df.assign(norm=df["narration"].map(normalize))
    df = df[(df["norm"].str.len() >= 2) & (df["amount"] > 0)]
    stats["after_dropping_invalid"] = len(df)

    key = ["norm", "type"]
    votes = df.groupby(key)["category"].value_counts(normalize=True).rename("share").reset_index()
    best = votes.sort_values("share", ascending=False).drop_duplicates(key)
    best["label"] = np.where(best["share"] >= majority, best["category"], "OTHER")
    df = df.merge(best[key + ["label"]], on=key)
    stats["relabelled_ambiguous"] = int((df["category"] != df["label"]).sum())
    df = df.assign(category=df["label"]).drop(columns="label")

    log_amt = np.log(df["amount"])
    z = (log_amt - log_amt.groupby(df["category"]).transform("mean")) / log_amt.groupby(df["category"]).transform("std")
    df = df[z.abs().fillna(0) <= z_max]
    stats["after_dropping_amount_outliers"] = len(df)

    df = df.assign(amt=df["amount"].map(amount_token))
    df = df.drop_duplicates(key + ["amt", "category"]).drop(columns=["norm", "amt"]).reset_index(drop=True)
    stats["after_dropping_duplicates"] = len(df)
    return df, stats


def groups(df: pd.DataFrame) -> np.ndarray:
    """Rows of the same merchant share a group; people and one-off rows are their own group."""
    named = ~df["merchant_id"].isin(["PERSON"]) & (df["merchant_id"] != df["category"])
    return np.where(named, df["merchant_id"], "row" + df.index.astype(str))


def group_folds(df: pd.DataFrame, n_splits: int, seed: int):
    cv = StratifiedGroupKFold(n_splits=n_splits, shuffle=True, random_state=seed)
    return cv.split(df, df["category"], groups(df))


def split(df: pd.DataFrame, test_size: float, seed: int) -> tuple[np.ndarray, np.ndarray]:
    return next(group_folds(df, round(1 / test_size), seed))


def random_split(df: pd.DataFrame, test_size: float, seed: int) -> tuple[np.ndarray, np.ndarray]:
    return train_test_split(np.arange(len(df)), test_size=test_size, stratify=df["category"], random_state=seed)


def load_real(cfg: dict[str, Any]) -> pd.DataFrame:
    df = pd.read_csv(path(cfg["data"]["real_path"]), usecols=["narration", "type", "mode", "amount"],
                     dtype={"narration": str})
    df = df.dropna(subset=["narration"]).drop_duplicates(["narration", "type"])
    labels = pd.read_csv(path(cfg["data"]["real_labels_path"]), dtype={"narration": str})
    return df.merge(labels, on=["narration", "type"], how="left").reset_index(drop=True)


def load_statement_truth(file: Path) -> pd.DataFrame:
    """Ground-truth transactions from a Priya-rk/Indian-Bank-Statements JSON, in parser columns."""
    rows = []
    for t in json.loads(Path(file).read_text(encoding="utf-8"))["transactions"]:
        if "cr_dr" in t:
            credit = t["cr_dr"] == "CR"
            amount, balance = t["transaction_amount"], t["available_balance"]
            date = pd.to_datetime(t["date"], format="%d/%m/%Y")
        else:
            credit = bool(t["credit"])
            amount, balance = t["credit"] or t["debit"] or 0.0, t["balance"]
            date = pd.to_datetime(t["date"][:10])
        if amount:
            rows.append({"date": date, "narration": t["description"], "type": "CREDIT" if credit else "DEBIT",
                         "amount": amount, "balance": balance})
    return pd.DataFrame(rows)
