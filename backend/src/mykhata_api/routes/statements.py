import hashlib
import os
from collections import Counter
import tempfile
import uuid
from pathlib import Path
from typing import Annotated

from fastapi import APIRouter, File, Form, HTTPException, Request, UploadFile, status
from sqlalchemy import select

from mykhata_api.db import Statement, Transaction
from mykhata_api.deps import CurrentUser, Db
from mykhata_api.routes.transactions import to_paise
from mykhata_api.schemas import StatementOut
from mykhata_ml import export, statement

router = APIRouter(prefix="/api/statements", tags=["statements"])

ALLOWED = {".pdf", ".csv"}
CHUNK = 1024 * 1024


def read_limited(upload: UploadFile, max_bytes: int) -> bytes:
    data = bytearray()
    while chunk := upload.file.read(CHUNK):
        data.extend(chunk)
        if len(data) > max_bytes:
            raise HTTPException(status.HTTP_413_CONTENT_TOO_LARGE,
                                f"The file is larger than {max_bytes // CHUNK} MB. Download a shorter date range.")
    if not data:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "The file is empty.")
    return bytes(data)


@router.get("", response_model=list[StatementOut])
def list_statements(user: CurrentUser, db: Db) -> list[Statement]:
    return list(db.scalars(select(Statement).where(Statement.user_id == user.id).order_by(Statement.uploaded_at.desc())))


@router.post("", response_model=StatementOut, status_code=status.HTTP_201_CREATED)
def upload_statement(request: Request, user: CurrentUser, db: Db, file: Annotated[UploadFile, File()],
                     password: Annotated[str | None, Form(max_length=128)] = None) -> Statement:
    name = Path(file.filename or "statement").name[:255]
    suffix = Path(name).suffix.lower()
    if suffix not in ALLOWED:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Upload a PDF or CSV bank statement.")
    content = read_limited(file, request.app.state.settings["max_upload_mb"] * CHUNK)
    digest = hashlib.sha256(content).hexdigest()
    if db.scalar(select(Statement.id).where(Statement.user_id == user.id, Statement.sha256 == digest)):
        raise HTTPException(status.HTTP_409_CONFLICT, "You have already uploaded this statement.")

    fd, tmp = tempfile.mkstemp(suffix=suffix)
    try:
        with os.fdopen(fd, "wb") as handle:
            handle.write(content)
        tx = export.categorise_statement(request.app.state.model, Path(tmp), user.confidence_threshold, password or None)
    except statement.StatementError as exc:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, str(exc)) from exc
    finally:
        Path(tmp).unlink(missing_ok=True)

    first, last = tx["date"].min().date(), tx["date"].max().date()
    # Counted, not a set: two identical ₹10 payments on one day are two real transactions.
    existing = Counter((t.date, t.narration, t.type, t.amount_paise) for t in db.scalars(
        select(Transaction).where(Transaction.user_id == user.id, Transaction.date.between(first, last))))
    record = Statement(user_id=user.id, filename=name, sha256=digest, period_start=first, period_end=last,
                       rows=len(tx), added=0, categorised=int((tx["category"] != "OTHER").sum()),
                       balance_failures=int((~tx["balance_ok"]).sum()))
    db.add(record)
    db.flush()
    for row in tx.itertuples():
        key = (row.date.date(), str(row.narration)[:512], row.type, to_paise(row.amount))
        if existing[key] > 0:
            existing[key] -= 1
            continue
        db.add(Transaction(id=str(uuid.uuid4()), user_id=user.id, statement_id=record.id, date=key[0], narration=key[1],
                           type=row.type, amount_paise=key[3], category=row.category, confidence=float(row.confidence),
                           balance_ok=bool(row.balance_ok), source="statement"))
        record.added += 1
    db.commit()
    return record
