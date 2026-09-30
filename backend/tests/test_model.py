import shutil
import subprocess

import pytest

from mykhata_ml import export
from mykhata_ml.categories import CATEGORIES
from mykhata_ml.config import load_config, path

CFG = load_config()
ARTIFACTS = path(CFG["output"]["artifacts"])

pytestmark = pytest.mark.skipif(not (ARTIFACTS / export.MODEL_FILE).exists(), reason="run scripts/train.py first")


@pytest.fixture(scope="module")
def pipe():
    return export.load(ARTIFACTS)


def test_header_matches_categories(pipe) -> None:
    assert set(pipe.classes_) == set(CATEGORIES) == set(pipe.header["categories"])


def test_tampered_model_is_rejected(tmp_path) -> None:
    raw = bytearray((ARTIFACTS / export.MODEL_FILE).read_bytes())
    raw[-1] ^= 0xFF
    (tmp_path / export.MODEL_FILE).write_bytes(raw)
    with pytest.raises(ValueError, match="integrity"):
        export.load(tmp_path)


@pytest.mark.skipif(shutil.which("node") is None, reason="Node.js not installed")
def test_typescript_runtime_matches_python() -> None:
    run = subprocess.run(["node", "--test", "web/parity.test.ts"], cwd=path("."), capture_output=True, text=True)
    assert run.returncode == 0, run.stdout + run.stderr


@pytest.mark.parametrize("narration,type_,expected", [
    ("UPI/DR/412345678901/SWIGGY/YESB/swiggy@ybl/UPI", "DEBIT", "FOOD_DINING"),
    ("POS 416021XXXXXX1234 DMART MUMBAI", "DEBIT", "GROCERIES"),
    ("ACH D- BAJAJ FINANCE LTD-P400XYZ123", "DEBIT", "EMI_LOAN"),
    ("NWD-416021XXXXXX1234-SPCNA123-PUNE", "DEBIT", "CASH_WITHDRAWAL"),
    ("NEFT CR-CITI0000002-INFOSYS LIMITED-RAHUL SHARMA-CITIN24123456-SALARY SEP 24", "CREDIT", "SALARY"),
    ("UPI-ZERODHA BROKING-zerodha@hdfcbank-HDFC0000001-412345678901-SIP", "DEBIT", "INVESTMENT"),
    ("Int.Pd:12345678901:01-04-2024 to 30-06-2024", "CREDIT", "INTEREST"),
    ("NETFLIX", "DEBIT", "ENTERTAINMENT"),
])
def test_known_narrations(pipe, narration, type_, expected) -> None:
    out = export.categorise(pipe, [narration], [type_], [500.0], CFG["default_threshold"])
    assert out["predicted"].iloc[0] == expected


def test_low_confidence_falls_back_to_other(pipe) -> None:
    out = export.categorise(pipe, ["zzqx"], ["DEBIT"], [10.0], threshold=1.01)
    assert out["category"].iloc[0] == "OTHER"
