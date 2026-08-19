"""
Pydantic models for request/response validation.
These models ensure data integrity before hitting the database.
"""

from pydantic import BaseModel, Field
from typing import Optional
from enum import Enum


# ============================================================
# Enums
# ============================================================

class AccountType(str, Enum):
    DEBIT = "debit"
    CREDIT = "credit"
    SAVINGS = "savings"


class TransactionType(str, Enum):
    INCOME = "income"
    EXPENSE = "expense"
    TRANSFER = "transfer"


class DebtStatus(str, Enum):
    ACTIVE = "active"
    PAID = "paid"


class LoanStatus(str, Enum):
    ACTIVE = "active"
    PAID = "paid"
    PARTIAL = "partial"


class SavingsMovementType(str, Enum):
    DEPOSIT = "deposit"
    WITHDRAWAL = "withdrawal"


# ============================================================
# Account Models
# ============================================================

class AccountCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    bank: str = Field(..., min_length=1, max_length=100)
    type: AccountType
    balance: float = Field(default=0, ge=0)
    available_balance: Optional[float] = None
    credit_limit: Optional[float] = None
    statement_day: Optional[int] = Field(None, ge=1, le=31)
    payment_day: Optional[int] = Field(None, ge=1, le=31)
    interest_rate: Optional[float] = None
    notes: Optional[str] = None


class AccountUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    bank: Optional[str] = Field(None, min_length=1, max_length=100)
    balance: Optional[float] = None
    available_balance: Optional[float] = None
    credit_limit: Optional[float] = None
    statement_day: Optional[int] = Field(None, ge=1, le=31)
    payment_day: Optional[int] = Field(None, ge=1, le=31)
    interest_rate: Optional[float] = None
    notes: Optional[str] = None
    active: Optional[int] = Field(None, ge=0, le=1)
    current_payment: Optional[float] = None


# ============================================================
# Category Models
# ============================================================

class CategoryCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    level: int = Field(default=0, ge=0, le=1)
    parent_id: Optional[int] = None
    icon: str = Field(default="📦", max_length=10)
    monthly_budget: Optional[float] = Field(None, ge=0)


# ============================================================
# Transaction Models
# ============================================================

class TransactionCreate(BaseModel):
    date: str = Field(..., pattern=r"^\d{4}-\d{2}-\d{2}$")
    type: TransactionType
    amount: float = Field(..., gt=0)
    category_id: Optional[int] = None
    description: Optional[str] = None
    method: Optional[str] = None
    tags: Optional[str] = None
    account_id: Optional[int] = None
    account_dest_id: Optional[int] = None


# ============================================================
# Debt Models
# ============================================================

class DebtCreate(BaseModel):
    creditor: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None
    original_amount: float = Field(..., gt=0)
    pending_balance: float = Field(..., ge=0)
    interest_rate: Optional[float] = None
    due_date: Optional[str] = Field(None, pattern=r"^\d{4}-\d{2}-\d{2}$")
    status: DebtStatus = DebtStatus.ACTIVE
    priority: int = Field(default=3, ge=1, le=3)


class DebtPaymentCreate(BaseModel):
    debt_id: int
    date: str = Field(..., pattern=r"^\d{4}-\d{2}-\d{2}$")
    amount: float = Field(..., gt=0)
    note: Optional[str] = None


# ============================================================
# Monthly Payment (MSI) Models
# ============================================================

class MonthlyPaymentCreate(BaseModel):
    account_id: int
    description: str = Field(..., min_length=1, max_length=200)
    total_amount: float = Field(..., gt=0)
    total_months: int = Field(..., gt=0)
    remaining_months: int = Field(..., ge=0)
    monthly_payment: float = Field(..., gt=0)
    start_date: Optional[str] = Field(None, pattern=r"^\d{4}-\d{2}-\d{2}$")
    end_date: Optional[str] = Field(None, pattern=r"^\d{4}-\d{2}-\d{2}$")
    note: Optional[str] = None


# ============================================================
# Fixed Expense Models
# ============================================================

class FixedExpenseCreate(BaseModel):
    description: str = Field(..., min_length=1, max_length=200)
    category_id: Optional[int] = None
    account_id: Optional[int] = None
    amount: float = Field(..., gt=0)
    payment_day: Optional[int] = Field(None, ge=1, le=31)
    active: int = Field(default=1, ge=0, le=1)
    notes: Optional[str] = None


# ============================================================
# Active Loan Models (money others owe to user)
# ============================================================

class ActiveLoanCreate(BaseModel):
    person: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None
    lent_amount: float = Field(..., gt=0)
    pending_balance: float = Field(..., ge=0)
    loan_date: Optional[str] = Field(None, pattern=r"^\d{4}-\d{2}-\d{2}$")
    due_date: Optional[str] = Field(None, pattern=r"^\d{4}-\d{2}-\d{2}$")
    status: LoanStatus = LoanStatus.ACTIVE
    priority: int = Field(default=3, ge=1, le=3)
    notes: Optional[str] = None


class LoanPaymentCreate(BaseModel):
    loan_id: int
    date: str = Field(..., pattern=r"^\d{4}-\d{2}-\d{2}$")
    amount: float = Field(..., gt=0)
    note: Optional[str] = None


# ============================================================
# Savings Models
# ============================================================

class SavingsCreate(BaseModel):
    account_id: int
    name: str = Field(..., min_length=1, max_length=100)
    amount: float = Field(default=0, ge=0)
    goal: Optional[float] = Field(None, gt=0)
    goal_date: Optional[str] = Field(None, pattern=r"^\d{4}-\d{2}-\d{2}$")
    active: int = Field(default=1, ge=0, le=1)
    notes: Optional[str] = None


class SavingsMovementCreate(BaseModel):
    savings_id: int
    type: SavingsMovementType
    amount: float = Field(..., gt=0)
    date: str = Field(..., pattern=r"^\d{4}-\d{2}-\d{2}$")
    note: Optional[str] = None


# ============================================================
# Budget Models
# ============================================================

class BudgetCreate(BaseModel):
    category_id: int
    month: str = Field(..., pattern=r"^\d{4}-\d{2}$")
    limit_amount: float = Field(..., gt=0)


# ============================================================
# Asset Models
# ============================================================

class AssetCreate(BaseModel):
    purchase_date: str = Field(..., pattern=r"^\d{4}-\d{2}-\d{2}$")
    item: str = Field(..., min_length=1, max_length=200)
    price: float = Field(..., gt=0)
    category: Optional[str] = None
    where_bought: Optional[str] = None
    notes: Optional[str] = None


# ============================================================
# Response Models
# ============================================================

class ToolResponse(BaseModel):
    success: bool
    data: Optional[dict | list] = None
    error: Optional[str] = None
    message: Optional[str] = None
