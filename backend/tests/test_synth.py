from mykhata_ml.categories import CATEGORIES
from mykhata_ml.synth import NarrationGenerator


def rows(n=3000, seed=1, sampling="balanced"):
    return list(NarrationGenerator(seed).generate(n, sampling=sampling))


def test_deterministic() -> None:
    assert rows(200) == rows(200)


def test_covers_every_category_with_valid_rows() -> None:
    out = rows()
    assert {r["category"] for r in out} == set(CATEGORIES)
    for r in out:
        assert r["narration"].strip()
        assert r["amount"] > 0
        direction = CATEGORIES[r["category"]]["direction"]
        assert direction == "BOTH" or r["type"] == direction


def test_bank_formats_appear() -> None:
    text = " ".join(r["narration"] for r in rows())
    for marker in ("UPI/DR/", "UPI/P2M/", "NEFT CR-", "ACH D-", "POS ", "BIL/BPAY/"):
        assert marker in text
