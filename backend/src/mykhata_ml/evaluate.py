"""Metrics, merchant-grouped CV, confidence/calibration tables, baselines and parser scores."""

from typing import Any

import numpy as np
import pandas as pd
import time

from sklearn.dummy import DummyClassifier
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix, f1_score
from sklearn.naive_bayes import ComplementNB
from sklearn.pipeline import make_pipeline
from sklearn.svm import LinearSVC

from mykhata_ml import data
from mykhata_ml import model as mdl


def metrics(y_true, y_pred) -> dict[str, float]:
    return {"accuracy": accuracy_score(y_true, y_pred),
            "macro_f1": f1_score(y_true, y_pred, average="macro"),
            "weighted_f1": f1_score(y_true, y_pred, average="weighted")}


def per_class(y_true, y_pred) -> dict[str, dict[str, float]]:
    report = classification_report(y_true, y_pred, output_dict=True, zero_division=0)
    return {k: v for k, v in report.items() if k not in ("accuracy", "macro avg", "weighted avg")}


def cross_validate(df: pd.DataFrame, cfg: dict[str, Any], seed: int) -> list[dict[str, float]]:
    texts = np.array(data.texts(df), dtype=object)
    y = df["category"].to_numpy()
    results = []
    for i, (tr, va) in enumerate(data.group_folds(df, cfg["split"]["cv_folds"], seed)):
        pipe = mdl.train(list(texts[tr]), y[tr], cfg["model"], seed)
        results.append({"fold": i + 1, **metrics(y[va], pipe.predict(list(texts[va])))})
    return results


def threshold_table(y_true, proba: np.ndarray, classes, thresholds: list[float]) -> list[dict[str, float]]:
    confident = proba.max(1)
    correct = np.asarray(classes)[proba.argmax(1)] == np.asarray(y_true)
    rows = []
    for t in thresholds:
        answered = confident >= t
        rows.append({"threshold": t, "coverage": answered.mean(),
                     "accuracy_answered": correct[answered].mean() if answered.any() else float("nan")})
    return rows


def real(y_true, y_pred) -> dict[str, float]:
    y_true, y_pred = np.asarray(y_true), np.asarray(y_pred)
    informative = y_true != "OTHER"
    correct = y_true == y_pred
    return {"rows": len(y_true), "accuracy": correct.mean(),
            "informative_rows": int(informative.sum()), "informative_accuracy": correct[informative].mean(),
            "opaque_kept_as_other": correct[~informative].mean()}


def parser_scores(parsed: pd.DataFrame, truth: pd.DataFrame) -> dict[str, float]:
    squash = lambda s: s.str.replace(r"\s+", "", regex=True)
    n = min(len(parsed), len(truth))
    p, t = parsed.iloc[:n].reset_index(drop=True), truth.iloc[:n].reset_index(drop=True)
    return {"truth_rows": len(truth), "parsed_rows": len(parsed),
            "date": (p["date"] == t["date"]).sum() / len(truth),
            "amount": ((p["amount"] - t["amount"]).abs() < 0.005).sum() / len(truth),
            "type": (p["type"] == t["type"]).sum() / len(truth),
            "balance": ((p["balance"] - t["balance"]).abs() < 0.005).sum() / len(truth),
            "narration_exact": (p["narration"] == t["narration"]).sum() / len(truth),
            "narration_ignoring_spaces": (squash(p["narration"]) == squash(t["narration"])).sum() / len(truth)}


def calibration(y_true, proba: np.ndarray, classes, bins: int = 10) -> dict:
    confidence = proba.max(1)
    correct = np.asarray(classes)[proba.argmax(1)] == np.asarray(y_true)
    edges = np.linspace(0, 1, bins + 1)
    rows, ece = [], 0.0
    for lo, hi in zip(edges[:-1], edges[1:]):
        inside = (confidence > lo) & (confidence <= hi)
        if inside.any():
            gap = abs(correct[inside].mean() - confidence[inside].mean())
            ece += inside.mean() * gap
            rows.append({"bin": f"{lo:.1f}-{hi:.1f}", "count": int(inside.sum()),
                         "confidence": confidence[inside].mean(), "accuracy": correct[inside].mean()})
    return {"ece": ece, "bins": rows}


def confusion(y_true, y_pred, labels) -> list[list[int]]:
    return confusion_matrix(y_true, y_pred, labels=labels).tolist()


def by_counterparty(test: pd.DataFrame, y_pred) -> dict[str, dict[str, float]]:
    kind = np.select([test["merchant_id"].str.startswith("LOCAL:"), test["merchant_id"].eq("PERSON"),
                      test["merchant_id"].str.startswith("EMPLOYER:"), test["merchant_id"].eq(test["category"])],
                     ["Local shops", "People", "Employers", "Fixed patterns"], "Brands")
    ok = pd.Series(np.asarray(y_pred) == test["category"].to_numpy())
    return {k: {"accuracy": float(ok[kind == k].mean()), "rows": int((kind == k).sum())} for k in np.unique(kind)}


KEYWORDS = {"atm": "CASH_WITHDRAWAL", "cash wdl": "CASH_WITHDRAWAL", "salary": "SALARY", "sal ": "SALARY",
            "interest": "INTEREST", "int.pd": "INTEREST", "emi": "EMI_LOAN", "loan": "EMI_LOAN", "rent": "RENT",
            "refund": "REFUND_CASHBACK", "cashback": "REFUND_CASHBACK", "reversal": "REFUND_CASHBACK",
            "chg": "BANK_CHARGES", "charges": "BANK_CHARGES", "self": "SELF_TRANSFER", "cash dep": "SELF_TRANSFER",
            "dividend": "INVESTMENT_RETURN", "sip": "INVESTMENT", "premium": "INSURANCE", "recharge": "BILLS_UTILITIES",
            "credit card": "CREDIT_CARD_BILL", "petrol": "FUEL", "fees": "EDUCATION"}


class KeywordLookup:
    """Rule-based baseline like typical expense apps: longest brand alias or keyword found wins, else OTHER."""

    def fit(self, aliases: dict[str, str]):
        rules = {**KEYWORDS, **{a.lower(): c for a, c in aliases.items()}}
        self.aliases = sorted(rules.items(), key=lambda ac: -len(ac[0]))
        return self

    def predict(self, texts):
        return np.array([next((c for a, c in self.aliases if a in t), "OTHER") for t in texts])


def baselines() -> dict:
    words = dict(token_pattern=r"[a-z0]+", sublinear_tf=True)
    chars = dict(analyzer="char_wb", ngram_range=(2, 5), sublinear_tf=True, max_features=60000)
    return {
        "Majority class": lambda: DummyClassifier(strategy="most_frequent"),
        "Brand keyword lookup": KeywordLookup,
        "Word TF-IDF + logistic regression": lambda: make_pipeline(
            TfidfVectorizer(**words), LogisticRegression(C=10, solver="saga", tol=1e-3, max_iter=200)),
        "Char TF-IDF + naive Bayes": lambda: make_pipeline(TfidfVectorizer(**chars), ComplementNB(alpha=0.1)),
        "Char + word TF-IDF + linear SVM": lambda: make_pipeline(
            TfidfVectorizer(**chars), LinearSVC(C=0.5)),
    }


def benchmark(df: pd.DataFrame, splits: dict, real: pd.DataFrame, aliases_by_row: pd.Series) -> dict[str, dict]:
    results = {}
    for name, make in baselines().items():
        row = {}
        for split, (tr, te) in splits.items():
            train, test = df.iloc[tr], df.iloc[te]
            model = make()
            start = time.perf_counter()
            if isinstance(model, KeywordLookup):
                model.fit({a: c for pairs in aliases_by_row.iloc[tr].dropna() for a, c in pairs})
                test_texts = test["narration"].str.lower().tolist()
            else:
                model.fit(data.texts(train), train["category"])
                test_texts = data.texts(test)
            row[f"{split}_train_seconds"] = time.perf_counter() - start
            pred = model.predict(test_texts)
            row[f"{split}_accuracy"] = accuracy_score(test["category"], pred)
            row[f"{split}_macro_f1"] = f1_score(test["category"], pred, average="macro")
            if split == "seen":
                real_texts = (real["narration"].str.lower().tolist() if isinstance(model, KeywordLookup)
                              else data.model_text(real["narration"], real["type"], real["amount"]))
                row["real_accuracy"] = accuracy_score(real["category"], model.predict(real_texts))
        row["abstains"] = hasattr(model, "predict_proba") and name != "Majority class"
        results[name] = row
    return results
