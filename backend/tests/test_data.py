import pandas as pd

from mykhata_ml import data
from mykhata_ml.synth import NarrationGenerator


def frame(n=4000):
    return pd.DataFrame(NarrationGenerator(7).generate(n, sampling="balanced"))


def test_normalize() -> None:
    assert data.normalize("  UPI/DR/412345678901/SWIGGY  ") == "upi/dr/0/swiggy"


def test_model_text_adds_direction_and_amount() -> None:
    assert data.model_text(["AMZN"], ["credit"], [1000]) == ["txcredit amt9 amzn"]


def test_split_keeps_merchants_on_one_side() -> None:
    df = frame()
    tr, te = data.split(df, 0.2, 42)
    g = data.groups(df)
    assert not set(tr) & set(te)
    assert not set(g[tr]) & set(g[te])
    assert set(df.iloc[te]["category"]) == set(df["category"])


def test_people_are_not_one_group() -> None:
    df = frame()
    g = data.groups(df)
    people = g[(df["merchant_id"] == "PERSON").to_numpy()]
    assert len(set(people)) == len(people)


def test_clean_resolves_conflicts_and_duplicates() -> None:
    df = pd.DataFrame({
        "narration": ["NEFT", "NEFT", "UPI/DR/111/SWIGGY", "UPI/DR/222/SWIGGY", "0", "AMZN"],
        "type": ["DEBIT"] * 6, "amount": [100.0, 200.0, 300.0, 300.0, 50.0, -5.0],
        "category": ["SALARY", "RENT", "FOOD_DINING", "FOOD_DINING", "OTHER", "SHOPPING"],
        "merchant_id": ["x"] * 6,
    })
    out, stats = data.clean(df)
    assert stats["after_dropping_invalid"] == 4
    assert set(out.loc[out["narration"] == "NEFT", "category"]) == {"OTHER"}
    assert (out["narration"].map(data.normalize) == "upi/dr/0/swiggy").sum() == 1
    assert not out.assign(amt=out["amount"].map(data.amount_token)).duplicated(["narration", "type", "amt", "category"]).any()
