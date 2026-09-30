from fastapi import APIRouter, HTTPException, status
from sqlalchemy import select

from mykhata_api.db import Budget
from mykhata_api.deps import CurrentUser, Db
from mykhata_api.routes.transactions import to_paise
from mykhata_api.schemas import BudgetIn, budgetable

router = APIRouter(prefix="/api/budgets", tags=["budgets"])


def valid(category: str) -> str:
    try:
        return budgetable(category)
    except ValueError as exc:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, str(exc)) from exc


@router.get("", response_model=dict[str, float])
def list_budgets(user: CurrentUser, db: Db) -> dict[str, float]:
    return {b.category: b.amount_paise / 100 for b in db.scalars(select(Budget).where(Budget.user_id == user.id))}


@router.put("/{category}", response_model=dict[str, float])
def set_budget(category: str, body: BudgetIn, user: CurrentUser, db: Db) -> dict[str, float]:
    category = valid(category)
    budget = db.get(Budget, (user.id, category)) or Budget(user_id=user.id, category=category)
    budget.amount_paise = to_paise(body.amount)
    db.merge(budget)
    db.commit()
    return {category: body.amount}


@router.delete("/{category}", status_code=status.HTTP_204_NO_CONTENT)
def delete_budget(category: str, user: CurrentUser, db: Db) -> None:
    if budget := db.get(Budget, (user.id, valid(category))):
        db.delete(budget)
        db.commit()
