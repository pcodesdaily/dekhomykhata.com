"""Saved model artifacts and the prediction helpers the app layer calls."""

import json
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.pipeline import Pipeline

from mykhata_ml import data, statement, web

MODEL_FILE = "model.mkm"


def save(pipe: Pipeline, artifacts: Path, threshold: float, golden_rows: pd.DataFrame) -> dict:
    artifacts.mkdir(parents=True, exist_ok=True)
    header = web.write(pipe, artifacts / MODEL_FILE, threshold)
    model = load(artifacts)
    out = categorise(model, golden_rows["narration"], golden_rows["type"], golden_rows["amount"], threshold)
    golden = [{"input": {"narration": str(r.narration), "type": r.type, "amount": float(r.amount)},
               "category": r.category, "confidence": float(r.confidence)} for r in out.itertuples()]
    (artifacts / "golden.json").write_text(json.dumps(golden), encoding="utf-8")
    return header


def load(artifacts: Path) -> web.WebModel:
    return web.WebModel(artifacts / MODEL_FILE)


def categorise(model, narrations, types, amounts, threshold: float) -> pd.DataFrame:
    proba = model.predict_proba(data.model_text(narrations, types, amounts))
    confidence = proba.max(1)
    predicted = model.classes_[proba.argmax(1)]
    return pd.DataFrame({"narration": list(narrations), "type": list(types), "amount": list(amounts),
                         "predicted": predicted,
                         "confidence": confidence.round(3),
                         "category": np.where(confidence >= threshold, predicted, "OTHER")})


def categorise_statement(model, file: Path, threshold: float, password: str | None = None) -> pd.DataFrame:
    tx = statement.load(file, password)
    out = categorise(model, tx["narration"], tx["type"], tx["amount"], threshold)
    return tx.assign(category=out["category"].to_numpy(), confidence=out["confidence"].to_numpy(),
                     balance_ok=statement.balance_check(tx))
