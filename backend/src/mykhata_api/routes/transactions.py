import uuid

from fastapi import APIRouter, HTTPException, Request, status
from sqlalchemy import select

from mykhata_api.db import Transaction
from mykhata_api.deps import CurrentUser, Db
from mykhata_api.schemas import (
    CategoriseIn, CategoriseOut, TransactionIn, TransactionOut, TransactionPatch, check_category,
)
from mykhata_ml import export

router = APIRouter(prefix="/api", tags=["transactions"])


def to_paise(rupees: float) -> int:
    return round(rupees * 100)


def serialize(t: Transaction) -> TransactionOut:
    return TransactionOut(id=t.id, date=t.date, narration=t.narration, type=t.type, amount=t.amount_paise / 100,
                          category=t.category, confidence=t.confidence, balance_ok=t.balance_ok, source=t.source,
                          note=t.note)


def predict(request: Request, narration: str, type_: str, amount: float) -> tuple[str, float]:
    row = export.categorise(request.app.state.model, [narration], [type_], [amount], 0.0).iloc[0]
    return str(row["predicted"]), float(row["confidence"])


def owned(db: Db, user_id: int, tx_id: str) -> Transaction:
    tx = db.get(Transaction, tx_id)
    if not tx or tx.user_id != user_id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Transaction not found")
    return tx


@router.get("/transactions", response_model=list[TransactionOut])
def list_transactions(user: CurrentUser, db: Db) -> list[TransactionOut]:
    rows = db.scalars(select(Transaction).where(Transaction.user_id == user.id)
                      .order_by(Transaction.date.desc(), Transaction.created_at.desc()))
    return [serialize(t) for t in rows]


@router.post("/transactions", response_model=TransactionOut, status_code=status.HTTP_201_CREATED)
def create_transaction(body: TransactionIn, request: Request, user: CurrentUser, db: Db) -> TransactionOut:
    category, confidence = body.category, None
    if category is None:
        category, confidence = predict(request, body.narration, body.type, body.amount)
        if confidence < user.confidence_threshold:
            category = "OTHER"
    tx = Transaction(id=str(uuid.uuid4()), user_id=user.id, date=body.date, narration=body.narration.strip(),
                     type=body.type, amount_paise=to_paise(body.amount), category=category, confidence=confidence,
                     source="manual", note=(body.note or None))
    db.add(tx)
    db.commit()
    return serialize(tx)


@router.patch("/transactions/{tx_id}", response_model=TransactionOut)
def update_transaction(tx_id: str, body: TransactionPatch, user: CurrentUser, db: Db) -> TransactionOut:
    tx = owned(db, user.id, tx_id)
    changes = body.model_dump(exclude_unset=True)
    try:
        check_category(changes.get("category", tx.category), changes.get("type", tx.type))
    except ValueError as exc:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, str(exc)) from exc
    if "amount" in changes:
        tx.amount_paise = to_paise(changes.pop("amount"))
    for key, value in changes.items():
        setattr(tx, key, value.strip() if isinstance(value, str) else value)
    if "category" in changes:
        tx.confidence = None
    db.commit()
    return serialize(tx)


@router.delete("/transactions/{tx_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_transaction(tx_id: str, user: CurrentUser, db: Db) -> None:
    db.delete(owned(db, user.id, tx_id))
    db.commit()


@router.post("/categorise", response_model=CategoriseOut)
def categorise(body: CategoriseIn, request: Request, _: CurrentUser) -> CategoriseOut:
    category, confidence = predict(request, body.narration, body.type, body.amount)
    return CategoriseOut(category=category, confidence=round(confidence, 2))
