import datetime as dt
from typing import Literal

from pydantic import BaseModel, ConfigDict, EmailStr, Field, model_validator

from mykhata_ml.categories import CATEGORIES

TxType = Literal["DEBIT", "CREDIT"]
MAX_RUPEES = 10_00_00_000


def check_category(category: str | None, type_: str | None) -> None:
    if category is None:
        return
    if category not in CATEGORIES:
        raise ValueError("Unknown category")
    direction = CATEGORIES[category]["direction"]
    if type_ and direction not in ("BOTH", type_):
        raise ValueError("This category doesn't match money in / money out")


class LoginIn(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1, max_length=128)


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    name: str
    email: str
    confidence_threshold: float


class UserPatch(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=80)
    confidence_threshold: float | None = Field(default=None, ge=0.3, le=0.9)


class TransactionIn(BaseModel):
    date: dt.date
    narration: str = Field(min_length=2, max_length=512)
    type: TxType
    amount: float = Field(gt=0, le=MAX_RUPEES)
    category: str | None = None
    note: str | None = Field(default=None, max_length=300)

    @model_validator(mode="after")
    def _valid(self):
        check_category(self.category, self.type)
        return self


class TransactionPatch(BaseModel):
    date: dt.date | None = None
    narration: str | None = Field(default=None, min_length=2, max_length=512)
    type: TxType | None = None
    amount: float | None = Field(default=None, gt=0, le=MAX_RUPEES)
    category: str | None = None
    note: str | None = Field(default=None, max_length=300)


class TransactionOut(BaseModel):
    id: str
    date: dt.date
    narration: str
    type: TxType
    amount: float
    category: str
    confidence: float | None
    balance_ok: bool | None
    source: str
    note: str | None


class CategoriseIn(BaseModel):
    narration: str = Field(min_length=1, max_length=512)
    type: TxType
    amount: float = Field(gt=0, le=MAX_RUPEES)


class CategoriseOut(BaseModel):
    category: str
    confidence: float


class BudgetIn(BaseModel):
    amount: float = Field(gt=0, le=MAX_RUPEES)


class StatementOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    filename: str
    period_start: dt.date | None
    period_end: dt.date | None
    rows: int
    added: int
    categorised: int
    balance_failures: int


def budgetable(category: str) -> str:
    if category not in CATEGORIES or CATEGORIES[category]["bucket"] not in ("need", "want"):
        raise ValueError("Budgets can only be set for spending categories")
    return category

