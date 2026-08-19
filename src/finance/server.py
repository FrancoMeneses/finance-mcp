"""
Finance MCP Server

Personal finance management via Model Context Protocol.
Provides tools for managing accounts, transactions, debts, savings, and more.

Usage:
    python server.py

Environment Variables:
    DB_PATH: Path to the SQLite database file
"""

import os
import logging
from pathlib import Path
from typing import Optional

from mcp.server.fastmcp import FastMCP

from finance.db import (
    get_accounts, get_account_by_id, create_account, update_account,
    get_categories, get_category_by_id,
    get_transactions, create_transaction,
    get_debts, get_debt_by_id, create_debt, create_debt_payment,
    get_monthly_payments, create_monthly_payment,
    get_fixed_expenses, create_fixed_expense,
    get_active_loans, create_active_loan, create_loan_payment,
    get_savings, get_savings_by_id, create_savings, create_savings_movement,
    get_savings_movements,
    get_budgets,
    get_assets, get_assets_summary,
    get_account_summary, get_monthly_summary,
)


# ============================================================
# Configuration
# ============================================================

LOG_DIR = Path(__file__).resolve().parent.parent / "logs"
LOG_DIR.mkdir(exist_ok=True)
LOG_FILE = LOG_DIR / "server.log"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Database path from environment or default
DB_PATH = os.environ.get("DB_PATH", str(Path(__file__).resolve().parent.parent / "finance.db"))


# ============================================================
# MCP Server
# ============================================================

mcp = FastMCP(
    "Finance",
    instructions="""Personal finance management tools.
    
    Use these tools to manage:
    - Accounts (bank accounts, credit cards, savings)
    - Transactions (income, expenses, transfers)
    - Debts and debt payments
    - Monthly payments (MSI/installments)
    - Fixed expenses
    - Active loans (money others owe)
    - Savings goals and movements
    - Budgets
    - Assets/net worth
    
    All monetary values are in MXN (Mexican Pesos).
    Dates should be in YYYY-MM-DD format.
    """
)


# ============================================================
# ACCOUNT TOOLS
# ============================================================

@mcp.tool()
def list_accounts(active_only: bool = True) -> list[dict]:
    """
    List all accounts (bank accounts, credit cards, savings).
    
    Args:
        active_only: If True, only return active accounts
    
    Returns:
        List of accounts with their details
    """
    logger.info("Listing accounts (active_only=%s)", active_only)
    return get_accounts(DB_PATH, active_only)


@mcp.tool()
def get_account(account_id: int) -> dict:
    """
    Get details of a specific account.
    
    Args:
        account_id: The account ID
    
    Returns:
        Account details
    """
    logger.info("Getting account %s", account_id)
    account = get_account_by_id(DB_PATH, account_id)
    if not account:
        return {"error": f"Account {account_id} not found"}
    return account


@mcp.tool()
def create_new_account(name: str, bank: str, account_type: str,
                       balance: float = 0, credit_limit: Optional[float] = None,
                       statement_day: Optional[int] = None,
                       payment_day: Optional[int] = None) -> dict:
    """
    Create a new account.
    
    Args:
        name: Account name (e.g., "Credit BBVA", "Debit MP")
        bank: Bank name (e.g., "BBVA", "MercadoPago")
        account_type: Type of account: "debit", "credit", or "savings"
        balance: Initial balance (default: 0)
        credit_limit: Credit limit (only for credit cards)
        statement_day: Statement day (only for credit cards, 1-31)
        payment_day: Payment day (only for credit cards, 1-31)
    
    Returns:
        Success message with new account ID
    """
    logger.info("Creating account: %s (%s)", name, account_type)
    try:
        result = create_account(
            DB_PATH, name, bank, account_type, balance,
            available_balance=balance,  # Initially available = total
            credit_limit=credit_limit,
            statement_day=statement_day,
            payment_day=payment_day
        )
        return result
    except Exception as e:
        return {"error": str(e)}


@mcp.tool()
def update_account_balance(account_id: int, balance: float,
                           available_balance: Optional[float] = None) -> dict:
    """
    Update an account's balance.
    
    Args:
        account_id: The account ID
        balance: New total balance
        available_balance: New available balance (if different from total)
    
    Returns:
        Success message
    """
    logger.info("Updating account %s balance to %s", account_id, balance)
    try:
        kwargs = {"balance": balance}
        if available_balance is not None:
            kwargs["available_balance"] = available_balance
        result = update_account(DB_PATH, account_id, **kwargs)
        return result
    except Exception as e:
        return {"error": str(e)}


# ============================================================
# CATEGORY TOOLS
# ============================================================

@mcp.tool()
def list_categories() -> list[dict]:
    """
    List all expense/income categories.
    
    Returns:
        List of categories with their hierarchy
    """
    logger.info("Listing categories")
    return get_categories(DB_PATH)


@mcp.tool()
def get_category(category_id: int) -> dict:
    """
    Get details of a specific category.
    
    Args:
        category_id: The category ID
    
    Returns:
        Category details
    """
    logger.info("Getting category %s", category_id)
    category = get_category_by_id(DB_PATH, category_id)
    if not category:
        return {"error": f"Category {category_id} not found"}
    return category


# ============================================================
# TRANSACTION TOOLS
# ============================================================

@mcp.tool()
def list_transactions(limit: int = 50, transaction_type: Optional[str] = None,
                      account_id: Optional[int] = None,
                      start_date: Optional[str] = None,
                      end_date: Optional[str] = None) -> list[dict]:
    """
    List transactions with optional filters.
    
    Args:
        limit: Max number of results (default: 50)
        transaction_type: Filter by type: "income", "expense", or "transfer"
        account_id: Filter by account ID
        start_date: Start date (YYYY-MM-DD)
        end_date: End date (YYYY-MM-DD)
    
    Returns:
        List of transactions
    """
    logger.info("Listing transactions (type=%s, account=%s)", transaction_type, account_id)
    return get_transactions(DB_PATH, limit, 0, transaction_type, account_id, start_date, end_date)


@mcp.tool()
def add_transaction(date: str, transaction_type: str, amount: float,
                    category_id: Optional[int] = None,
                    description: Optional[str] = None,
                    method: Optional[str] = None,
                    tags: Optional[str] = None,
                    account_id: Optional[int] = None,
                    account_dest_id: Optional[int] = None) -> dict:
    """
    Record a new transaction.
    
    Args:
        date: Transaction date (YYYY-MM-DD)
        transaction_type: "income", "expense", or "transfer"
        amount: Transaction amount (must be positive)
        category_id: Category ID (optional)
        description: Description (optional)
        method: Payment method: "cash", "card", "transfer" (optional)
        tags: Comma-separated tags (optional, e.g., "gasoline,moto")
        account_id: Source account ID
        account_dest_id: Destination account ID (only for transfers)
    
    Returns:
        Success message with new transaction ID
    """
    logger.info("Adding %s transaction: $%s on %s", transaction_type, amount, date)
    try:
        result = create_transaction(
            DB_PATH, date, transaction_type, amount,
            category_id, description, method, tags,
            account_id, account_dest_id
        )
        return result
    except Exception as e:
        return {"error": str(e)}


# ============================================================
# DEBT TOOLS
# ============================================================

@mcp.tool()
def list_debts(status: Optional[str] = None) -> list[dict]:
    """
    List debts (what the user owes).
    
    Args:
        status: Filter by status: "active" or "paid"
    
    Returns:
        List of debts
    """
    logger.info("Listing debts (status=%s)", status)
    return get_debts(DB_PATH, status)


@mcp.tool()
def get_debt(debt_id: int) -> dict:
    """
    Get details of a specific debt.
    
    Args:
        debt_id: The debt ID
    
    Returns:
        Debt details
    """
    logger.info("Getting debt %s", debt_id)
    debt = get_debt_by_id(DB_PATH, debt_id)
    if not debt:
        return {"error": f"Debt {debt_id} not found"}
    return debt


@mcp.tool()
def add_debt(creditor: str, original_amount: float, pending_balance: float,
             description: Optional[str] = None,
             interest_rate: Optional[float] = None,
             due_date: Optional[str] = None,
             priority: int = 3) -> dict:
    """
    Register a new debt.
    
    Args:
        creditor: Creditor name (e.g., "BBVA", "Nu", "CNC")
        original_amount: Original debt amount
        pending_balance: Current pending balance
        description: Description (optional)
        interest_rate: Annual interest rate (optional)
        due_date: Due date (YYYY-MM-DD, optional)
        priority: 1=high, 2=medium, 3=low (default: 3)
    
    Returns:
        Success message with new debt ID
    """
    logger.info("Adding debt: %s ($%s)", creditor, pending_balance)
    try:
        result = create_debt(
            DB_PATH, creditor, original_amount, pending_balance,
            description, interest_rate, due_date, "active", priority
        )
        return result
    except Exception as e:
        return {"error": str(e)}


@mcp.tool()
def record_debt_payment(debt_id: int, date: str, amount: float,
                        note: Optional[str] = None) -> dict:
    """
    Record a payment towards a debt.
    
    Args:
        debt_id: The debt ID
        date: Payment date (YYYY-MM-DD)
        amount: Payment amount
        note: Optional note
    
    Returns:
        Success message
    """
    logger.info("Recording debt payment: $%s for debt %s", amount, debt_id)
    try:
        result = create_debt_payment(DB_PATH, debt_id, date, amount, note)
        return result
    except Exception as e:
        return {"error": str(e)}


# ============================================================
# MONTHLY PAYMENT (MSI) TOOLS
# ============================================================

@mcp.tool()
def list_monthly_payments(account_id: Optional[int] = None) -> list[dict]:
    """
    List monthly payments (installments/MSI).
    
    Args:
        account_id: Filter by account ID (optional)
    
    Returns:
        List of monthly payments
    """
    logger.info("Listing monthly payments (account=%s)", account_id)
    return get_monthly_payments(DB_PATH, account_id)


@mcp.tool()
def add_monthly_payment(account_id: int, description: str,
                        total_amount: float, total_months: int,
                        remaining_months: int, monthly_payment: float,
                        start_date: Optional[str] = None,
                        end_date: Optional[str] = None,
                        note: Optional[str] = None) -> dict:
    """
    Register a new installment purchase (MSI).
    
    Args:
        account_id: Account ID where the purchase was made
        description: Description (e.g., "MSI BBVA - 6 months")
        total_amount: Total purchase amount
        total_months: Total number of months
        remaining_months: Months remaining to pay
        monthly_payment: Monthly payment amount
        start_date: Start date (YYYY-MM-DD, optional)
        end_date: End date (YYYY-MM-DD, optional)
        note: Optional note
    
    Returns:
        Success message with new ID
    """
    logger.info("Adding monthly payment: %s", description)
    try:
        result = create_monthly_payment(
            DB_PATH, account_id, description, total_amount,
            total_months, remaining_months, monthly_payment,
            start_date, end_date, note
        )
        return result
    except Exception as e:
        return {"error": str(e)}


# ============================================================
# FIXED EXPENSE TOOLS
# ============================================================

@mcp.tool()
def list_fixed_expenses(active_only: bool = True) -> list[dict]:
    """
    List fixed monthly expenses.
    
    Args:
        active_only: If True, only return active expenses
    
    Returns:
        List of fixed expenses
    """
    logger.info("Listing fixed expenses (active_only=%s)", active_only)
    return get_fixed_expenses(DB_PATH, active_only)


@mcp.tool()
def add_fixed_expense(description: str, amount: float,
                      category_id: Optional[int] = None,
                      account_id: Optional[int] = None,
                      payment_day: Optional[int] = None,
                      notes: Optional[str] = None) -> dict:
    """
    Add a new fixed monthly expense.
    
    Args:
        description: Expense name (e.g., "Internet", "Gym")
        amount: Monthly amount
        category_id: Category ID (optional)
        account_id: Account ID (optional)
        payment_day: Payment day of month (1-31, optional)
        notes: Optional notes
    
    Returns:
        Success message with new ID
    """
    logger.info("Adding fixed expense: %s ($%s)", description, amount)
    try:
        result = create_fixed_expense(
            DB_PATH, description, amount, category_id,
            account_id, payment_day, 1, notes
        )
        return result
    except Exception as e:
        return {"error": str(e)}


# ============================================================
# ACTIVE LOAN TOOLS (money others owe to user)
# ============================================================

@mcp.tool()
def list_active_loans(status: Optional[str] = None) -> list[dict]:
    """
    List active loans (money others owe to the user).
    
    Args:
        status: Filter by status: "active", "paid", or "partial"
    
    Returns:
        List of active loans
    """
    logger.info("Listing active loans (status=%s)", status)
    return get_active_loans(DB_PATH, status)


@mcp.tool()
def add_active_loan(person: str, lent_amount: float, pending_balance: float,
                    description: Optional[str] = None,
                    loan_date: Optional[str] = None,
                    due_date: Optional[str] = None,
                    priority: int = 3,
                    notes: Optional[str] = None) -> dict:
    """
    Register a loan given to someone.
    
    Args:
        person: Person's name who borrowed
        lent_amount: Total amount lent
        pending_balance: Amount still owed
        description: Description (optional)
        loan_date: Loan date (YYYY-MM-DD, optional)
        due_date: Due date (YYYY-MM-DD, optional)
        priority: 1=high, 2=medium, 3=low (default: 3)
        notes: Optional notes
    
    Returns:
        Success message with new ID
    """
    logger.info("Adding loan to %s: $%s", person, lent_amount)
    try:
        result = create_active_loan(
            DB_PATH, person, lent_amount, pending_balance,
            description, loan_date, due_date, "active", priority, notes
        )
        return result
    except Exception as e:
        return {"error": str(e)}


@mcp.tool()
def record_loan_payment(loan_id: int, date: str, amount: float,
                        note: Optional[str] = None) -> dict:
    """
    Record a payment received from someone who owed money.
    
    Args:
        loan_id: The loan ID
        date: Payment date (YYYY-MM-DD)
        amount: Payment amount
        note: Optional note
    
    Returns:
        Success message
    """
    logger.info("Recording loan payment: $%s for loan %s", amount, loan_id)
    try:
        result = create_loan_payment(DB_PATH, loan_id, date, amount, note)
        return result
    except Exception as e:
        return {"error": str(e)}


# ============================================================
# SAVINGS TOOLS
# ============================================================

@mcp.tool()
def list_savings(account_id: Optional[int] = None,
                 active_only: bool = True) -> list[dict]:
    """
    List savings goals.
    
    Args:
        account_id: Filter by account ID (optional)
        active_only: If True, only return active savings goals
    
    Returns:
        List of savings goals with amounts and goals
    """
    logger.info("Listing savings (account=%s, active=%s)", account_id, active_only)
    return get_savings(DB_PATH, account_id, active_only)


@mcp.tool()
def get_savings_goal(savings_id: int) -> dict:
    """
    Get details of a specific savings goal.
    
    Args:
        savings_id: The savings goal ID
    
    Returns:
        Savings goal details
    """
    logger.info("Getting savings goal %s", savings_id)
    goal = get_savings_by_id(DB_PATH, savings_id)
    if not goal:
        return {"error": f"Savings goal {savings_id} not found"}
    return goal


@mcp.tool()
def add_savings_goal(account_id: int, name: str,
                     amount: float = 0, goal: Optional[float] = None,
                     goal_date: Optional[str] = None,
                     notes: Optional[str] = None) -> dict:
    """
    Create a new savings goal.
    
    Args:
        account_id: Account ID where the savings are held
        name: Goal name (e.g., "Chetumal Trip", "450 MT")
        amount: Initial amount saved (default: 0)
        goal: Target amount (optional)
        goal_date: Target date (YYYY-MM-DD, optional)
        notes: Optional notes
    
    Returns:
        Success message with new ID
    """
    logger.info("Adding savings goal: %s", name)
    try:
        result = create_savings(
            DB_PATH, account_id, name, amount, goal, goal_date, 1, notes
        )
        return result
    except Exception as e:
        return {"error": str(e)}


@mcp.tool()
def record_savings_movement(savings_id: int, movement_type: str,
                            amount: float, date: str,
                            note: Optional[str] = None) -> dict:
    """
    Record a deposit or withdrawal to/from a savings goal.
    
    This automatically updates:
    - The savings goal amount
    - The account's available balance
    
    Args:
        savings_id: The savings goal ID
        movement_type: "deposit" (add money) or "withdrawal" (take money out)
        amount: Amount
        date: Movement date (YYYY-MM-DD)
        note: Optional note (e.g., "Quincena", "Emergency")
    
    Returns:
        Success message
    """
    logger.info("Recording %s: $%s for savings %s", movement_type, amount, savings_id)
    try:
        result = create_savings_movement(
            DB_PATH, savings_id, movement_type, amount, date, note
        )
        return result
    except Exception as e:
        return {"error": str(e)}


@mcp.tool()
def list_savings_movements(savings_id: int, limit: int = 50) -> list[dict]:
    """
    Get movement history for a savings goal.
    
    Args:
        savings_id: The savings goal ID
        limit: Max number of results (default: 50)
    
    Returns:
        List of movements
    """
    logger.info("Listing movements for savings %s", savings_id)
    return get_savings_movements(DB_PATH, savings_id, limit)


# ============================================================
# BUDGET TOOLS
# ============================================================

@mcp.tool()
def list_budgets(month: Optional[str] = None) -> list[dict]:
    """
    List budgets.
    
    Args:
        month: Filter by month (YYYY-MM format, optional)
    
    Returns:
        List of budgets
    """
    logger.info("Listing budgets (month=%s)", month)
    return get_budgets(DB_PATH, month)


# ============================================================
# ASSET TOOLS
# ============================================================

@mcp.tool()
def list_assets(category: Optional[str] = None) -> list[dict]:
    """
    List personal assets.
    
    Args:
        category: Filter by category (optional, e.g., "Moto", "Computing")
    
    Returns:
        List of assets
    """
    logger.info("Listing assets (category=%s)", category)
    return get_assets(DB_PATH, category)


@mcp.tool()
def get_assets_total() -> dict:
    """
    Get total value and count of all assets.
    
    Returns:
        Summary with total_value and count
    """
    logger.info("Getting assets summary")
    return get_assets_summary(DB_PATH)


# ============================================================
# SUMMARY TOOLS
# ============================================================

@mcp.tool()
def get_account_overview() -> dict:
    """
    Get a quick overview of all accounts.
    
    Returns:
        Summary of account types, balances, and total savings
    """
    logger.info("Getting account overview")
    return get_account_summary(DB_PATH)


@mcp.tool()
def get_monthly_report(year: int, month: int) -> dict:
    """
    Get income/expense report for a specific month.
    
    Args:
        year: Year (e.g., 2026)
        month: Month (1-12)
    
    Returns:
        Monthly summary with income, expenses, net, and breakdown by category
    """
    logger.info("Getting monthly report for %s-%02d", year, month)
    return get_monthly_summary(DB_PATH, year, month)


# ============================================================
# Entry Point
# ============================================================

if __name__ == "__main__":
    logger.info("Starting Finance MCP Server...")
    logger.info("Database: %s", DB_PATH)
    mcp.run()
