"""Bank-statement PDF or CSV -> transactions (date, narration, debit, credit, type, amount, balance)."""

import re
from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd
import pdfplumber
from pdfminer.pdfdocument import PDFPasswordIncorrect

MAX_BYTES = 20 * 1024 * 1024
MAX_PAGES = 300
COLUMNS = ["date", "narration", "debit", "credit", "type", "amount", "balance"]

HEADERS = {
    "date": ("txn date", "transaction date", "tran date", "date", "txn posted date", "posting date", "value date"),
    "narration": ("description", "narration", "particulars", "details", "remarks", "transaction details"),
    "debit": ("debit", "withdrawal", "withdrawals", "dr amount", "debit amount", "withdrawal amt"),
    "credit": ("credit", "deposit", "deposits", "cr amount", "credit amount", "deposit amt"),
    "amount": ("amount", "transaction amount", "txn amount"),
    "drcr": ("cr/dr", "dr/cr", "type", "cr / dr", "dr / cr"),
    "balance": ("balance", "available balance", "closing balance", "running balance"),
}
DATE_FORMATS = ("%d-%m-%Y", "%d/%m/%Y", "%d %b %Y", "%d-%b-%Y", "%d-%b-%y", "%d/%m/%y", "%d-%m-%y",
                "%Y-%m-%d", "%d.%m.%Y", "%d %B %Y")
_AMOUNT = re.compile(r"-?[\d,]+(?:\.\d+)?")
_SPACES = re.compile(r"\s+")


class StatementError(ValueError):
    pass


def _visible(obj) -> bool:
    """Drops watermark glyphs: rotated or oversized text."""
    return obj.get("object_type") != "char" or (abs(obj["matrix"][1]) < 0.01 and obj["size"] < 20)


def _clean(cell) -> str:
    return _SPACES.sub(" ", str(cell or "").replace("\n", " ")).strip()


def parse_amount(cell, signed: bool = False) -> float | None:
    text = _clean(cell).replace("Rs.", "").replace("INR", "").replace("₹", "").replace(" ", "")
    match = _AMOUNT.search(text)
    if not match or not any(ch.isdigit() for ch in match.group()):
        return None
    value = float(match.group().replace(",", ""))
    if not signed:
        return abs(value)
    return -abs(value) if text.upper().endswith("DR") else value


def parse_date(cell) -> pd.Timestamp | None:
    text = str(cell or "").strip().split("\n")[0].strip()
    for candidate in (text, " ".join(text.split()[:3]), text.split(" ")[0]):
        for fmt in DATE_FORMATS:
            try:
                return pd.Timestamp(datetime.strptime(candidate, fmt))
            except ValueError:
                continue
    return None


def _header_key(cell) -> str:
    """'Withdrawal Amt.' -> 'withdrawal amt', 'Cr / Dr' -> 'cr/dr' (banks vary punctuation and spacing)."""
    text = re.sub(r"[^a-z/ ]", "", _clean(cell).lower())
    return _SPACES.sub(" ", re.sub(r"\s*/\s*", "/", text)).strip()


def _header_map(row) -> dict[str, int] | None:
    cells = [_header_key(c) for c in row]
    found = {}
    for field, names in HEADERS.items():
        for name in names:
            free = [i for i, cell in enumerate(cells) if cell == name and i not in found.values()]
            if free:
                found[field] = free[0]
                break
    has_money = {"debit", "credit"} <= found.keys() or {"amount", "drcr"} <= found.keys()
    return found if {"date", "narration", "balance"} <= found.keys() and has_money else None


def _row(cells, cols: dict[str, int]) -> dict | None:
    get = lambda f: cells[cols[f]] if f in cols and cols[f] < len(cells) else None
    date = parse_date(get("date"))
    if date is None:
        return None
    if "amount" in cols and "drcr" in cols:
        amount, flag = parse_amount(get("amount")), _clean(get("drcr")).upper()
        is_credit = "CR" in flag
        debit, credit = (None, amount) if is_credit else (amount, None)
    else:
        debit, credit = parse_amount(get("debit")), parse_amount(get("credit"))
    amount = credit if credit else debit
    if not amount:
        return None
    return {"date": date, "narration": _clean(get("narration")), "debit": debit, "credit": credit,
            "type": "CREDIT" if credit else "DEBIT", "amount": amount, "balance": parse_amount(get("balance"), signed=True)}


def parse(file: str | Path, password: str | None = None) -> pd.DataFrame:
    file = Path(file)
    if file.stat().st_size > MAX_BYTES:
        raise StatementError("file is larger than 20 MB")
    if file.read_bytes()[:5] != b"%PDF-":
        raise StatementError("not a PDF file")
    try:
        pdf = pdfplumber.open(file, password=password or "")
    except PDFPasswordIncorrect as exc:
        raise StatementError("PDF is password protected: pass the statement password") from exc
    except Exception as exc:
        raise StatementError(f"could not read PDF: {exc}") from exc

    rows, cols, has_text = [], None, False
    with pdf:
        if len(pdf.pages) > MAX_PAGES:
            raise StatementError(f"more than {MAX_PAGES} pages")
        for page in pdf.pages:
            page = page.filter(_visible)
            has_text = has_text or bool(page.chars)
            for table in page.extract_tables():
                for cells in table:
                    cols = _header_map(cells) or cols
                    if cols and (row := _row(cells, cols)):
                        rows.append(row)
    if not has_text:
        raise StatementError("no text layer found: scanned statements are not supported yet")
    if not rows:
        raise StatementError("no transaction table found")
    return pd.DataFrame(rows, columns=COLUMNS)


def load_csv(file: str | Path) -> pd.DataFrame:
    """CSV exports: generic headers, or Account Aggregator style (type, amount, currentBalance, transactionTimestamp)."""
    raw = pd.read_csv(file, dtype=str).rename(columns=str.strip)
    lower = {c.lower(): c for c in raw.columns}
    pick = lambda *names: next((lower[n] for n in names if n in lower), None)
    date_col = pick("transactiontimestamp", *HEADERS["date"])
    narration_col = pick(*HEADERS["narration"])
    if not date_col or not narration_col:
        raise StatementError("CSV needs a date and a narration/description column")
    debit_col, credit_col = pick(*HEADERS["debit"]), pick(*HEADERS["credit"])
    type_col, amount_col = pick("type", *HEADERS["drcr"]), pick(*HEADERS["amount"])
    out = pd.DataFrame({"date": raw[date_col].fillna("").str[:10].map(parse_date),
                        "narration": raw[narration_col].fillna("").map(_clean)})
    if debit_col and credit_col:
        out["debit"], out["credit"] = raw[debit_col].map(parse_amount), raw[credit_col].map(parse_amount)
    elif type_col and amount_col:
        credit = raw[type_col].str.upper().str.startswith("C")
        amount = raw[amount_col].map(parse_amount)
        out["debit"], out["credit"] = amount.where(~credit), amount.where(credit)
    else:
        raise StatementError("CSV needs debit/credit columns, or type + amount columns")
    out["type"] = np.where(out["credit"].fillna(0) > 0, "CREDIT", "DEBIT")
    out["amount"] = out["credit"].fillna(0) + out["debit"].fillna(0)
    balance_col = pick("currentbalance", *HEADERS["balance"])
    out["balance"] = raw[balance_col].map(lambda c: parse_amount(c, signed=True)) if balance_col else np.nan
    out = out[out["date"].notna() & (out["amount"] > 0)].reset_index(drop=True)
    if out.empty:
        raise StatementError("no transactions found in CSV")
    return out[COLUMNS]


def load(file: str | Path, password: str | None = None) -> pd.DataFrame:
    return load_csv(file) if Path(file).suffix.lower() == ".csv" else parse(file, password)


def balance_check(df: pd.DataFrame, tolerance: float = 0.01) -> pd.Series:
    """True where previous balance +/- amount equals this row's balance (first row can't be checked)."""
    signed = df["amount"].where(df["type"] == "CREDIT", -df["amount"])
    expected = df["balance"].shift() + signed
    return ((expected - df["balance"]).abs() <= tolerance) | expected.isna()
