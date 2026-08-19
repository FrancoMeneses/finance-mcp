"""
Database access layer for Finance MCP.

All database operations go through this module.
Uses parameterized queries to prevent SQL injection.
"""

import sqlite3
from pathlib import Path
from typing import Optional
from datetime import datetime


# ============================================================
# Connection Management
# ============================================================

def get_connection(db_path: str) -> sqlite3.Connection:
    """Create and return a connection to the SQLite database."""
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row  # Return dicts instead of tuples
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def dict_from_row(row: sqlite3.Row) -> dict:
    """Convert a sqlite3.Row to a dictionary."""
    return dict(row) if row else None


# ============================================================
# ACCOUNTS
# ============================================================

def get_accounts(db_path: str, active_only: bool = True) -> list[dict]:
    """Get all accounts."""
    conn = get_connection(db_path)
    try:
        query = "SELECT * FROM accounts"
        if active_only:
            query += " WHERE active = 1"
        query += " ORDER BY name"
        rows = conn.execute(query).fetchall()
        return [dict_from_row(r) for r in rows]
    finally:
        conn.close()


def get_account_by_id(db_path: str, account_id: int) -> Optional[dict]:
    """Get a single account by ID."""
    conn = get_connection(db_path)
    try:
        row = conn.execute(
            "SELECT * FROM accounts WHERE id = ?", (account_id,)
        ).fetchone()
        return dict_from_row(row)
    finally:
        conn.close()


def create_account(db_path: str, name: str, bank: str, account_type: str,
                   balance: float = 0, available_balance: Optional[float] = None,
                   credit_limit: Optional[float] = None, statement_day: Optional[int] = None,
                   payment_day: Optional[int] = None, interest_rate: Optional[float] = None,
                   notes: Optional[str] = None) -> dict:
    """Create a new account."""
    conn = get_connection(db_path)
    try:
        cursor = conn.execute(
            """INSERT INTO accounts (name, bank, type, balance, available_balance,
               credit_limit, statement_day, payment_day, interest_rate, notes)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (name, bank, account_type, balance, available_balance,
             credit_limit, statement_day, payment_day, interest_rate, notes)
        )
        conn.commit()
        return {"id": cursor.lastrowid, "message": f"Account '{name}' created successfully"}
    except sqlite3.Error as e:
        conn.rollback()
        raise e
    finally:
        conn.close()


def update_account(db_path: str, account_id: int, **kwargs) -> dict:
    """Update an account. Only provided fields are updated."""
    allowed_fields = {
        'name', 'bank', 'balance', 'available_balance', 'credit_limit',
        'statement_day', 'payment_day', 'interest_rate', 'notes', 'active', 'current_payment'
    }
    updates = {k: v for k, v in kwargs.items() if k in allowed_fields and v is not None}

    if not updates:
        return {"message": "No fields to update"}

    conn = get_connection(db_path)
    try:
        set_clause = ", ".join(f"{k} = ?" for k in updates.keys())
        values = list(updates.values()) + [account_id]
        conn.execute(f"UPDATE accounts SET {set_clause} WHERE id = ?", values)
        conn.commit()
        return {"message": f"Account {account_id} updated successfully"}
    except sqlite3.Error as e:
        conn.rollback()
        raise e
    finally:
        conn.close()


# ============================================================
# CATEGORIES
# ============================================================

def get_categories(db_path: str) -> list[dict]:
    """Get all categories."""
    conn = get_connection(db_path)
    try:
        rows = conn.execute(
            "SELECT * FROM categories ORDER BY level, name"
        ).fetchall()
        return [dict_from_row(r) for r in rows]
    finally:
        conn.close()


def get_category_by_id(db_path: str, category_id: int) -> Optional[dict]:
    """Get a single category by ID."""
    conn = get_connection(db_path)
    try:
        row = conn.execute(
            "SELECT * FROM categories WHERE id = ?", (category_id,)
        ).fetchone()
        return dict_from_row(row)
    finally:
        conn.close()


# ============================================================
# TRANSACTIONS
# ============================================================

def get_transactions(db_path: str, limit: int = 50, offset: int = 0,
                     transaction_type: Optional[str] = None,
                     account_id: Optional[int] = None,
                     start_date: Optional[str] = None,
                     end_date: Optional[str] = None) -> list[dict]:
    """Get transactions with optional filters."""
    conn = get_connection(db_path)
    try:
        query = "SELECT * FROM transactions WHERE 1=1"
        params = []

        if transaction_type:
            query += " AND type = ?"
            params.append(transaction_type)
        if account_id:
            query += " AND (account_id = ? OR account_dest_id = ?)"
            params.extend([account_id, account_id])
        if start_date:
            query += " AND date >= ?"
            params.append(start_date)
        if end_date:
            query += " AND date <= ?"
            params.append(end_date)

        query += " ORDER BY date DESC, id DESC LIMIT ? OFFSET ?"
        params.extend([limit, offset])

        rows = conn.execute(query, params).fetchall()
        return [dict_from_row(r) for r in rows]
    finally:
        conn.close()


def create_transaction(db_path: str, date: str, transaction_type: str,
                       amount: float, category_id: Optional[int] = None,
                       description: Optional[str] = None, method: Optional[str] = None,
                       tags: Optional[str] = None, account_id: Optional[int] = None,
                       account_dest_id: Optional[int] = None) -> dict:
    """Create a new transaction and update account balances."""
    conn = get_connection(db_path)
    try:
        # Insert transaction
        cursor = conn.execute(
            """INSERT INTO transactions (date, type, amount, category_id, description,
               method, tags, account_id, account_dest_id)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (date, transaction_type, amount, category_id, description,
             method, tags, account_id, account_dest_id)
        )

        # Update account balances
        if account_id and transaction_type == "expense":
            conn.execute(
                "UPDATE accounts SET balance = balance - ? WHERE id = ?",
                (amount, account_id)
            )
        elif account_id and transaction_type == "income":
            conn.execute(
                "UPDATE accounts SET balance = balance + ? WHERE id = ?",
                (amount, account_id)
            )
        elif account_id and account_dest_id and transaction_type == "transfer":
            conn.execute(
                "UPDATE accounts SET balance = balance - ? WHERE id = ?",
                (amount, account_id)
            )
            conn.execute(
                "UPDATE accounts SET balance = balance + ? WHERE id = ?",
                (amount, account_dest_id)
            )

        conn.commit()
        return {"id": cursor.lastrowid, "message": "Transaction created successfully"}
    except sqlite3.Error as e:
        conn.rollback()
        raise e
    finally:
        conn.close()


# ============================================================
# DEBTS
# ============================================================

def get_debts(db_path: str, status: Optional[str] = None) -> list[dict]:
    """Get debts, optionally filtered by status."""
    conn = get_connection(db_path)
    try:
        query = "SELECT * FROM debts"
        params = []
        if status:
            query += " WHERE status = ?"
            params.append(status)
        query += " ORDER BY priority, pending_balance DESC"
        rows = conn.execute(query, params).fetchall()
        return [dict_from_row(r) for r in rows]
    finally:
        conn.close()


def get_debt_by_id(db_path: str, debt_id: int) -> Optional[dict]:
    """Get a single debt by ID."""
    conn = get_connection(db_path)
    try:
        row = conn.execute(
            "SELECT * FROM debts WHERE id = ?", (debt_id,)
        ).fetchone()
        return dict_from_row(row)
    finally:
        conn.close()


def create_debt(db_path: str, creditor: str, original_amount: float,
                pending_balance: float, description: Optional[str] = None,
                interest_rate: Optional[float] = None, due_date: Optional[str] = None,
                status: str = "active", priority: int = 3) -> dict:
    """Create a new debt."""
    conn = get_connection(db_path)
    try:
        cursor = conn.execute(
            """INSERT INTO debts (creditor, description, original_amount, pending_balance,
               interest_rate, due_date, status, priority)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (creditor, description, original_amount, pending_balance,
             interest_rate, due_date, status, priority)
        )
        conn.commit()
        return {"id": cursor.lastrowid, "message": f"Debt to '{creditor}' created successfully"}
    except sqlite3.Error as e:
        conn.rollback()
        raise e
    finally:
        conn.close()


def create_debt_payment(db_path: str, debt_id: int, date: str,
                        amount: float, note: Optional[str] = None) -> dict:
    """Record a debt payment and update pending balance."""
    conn = get_connection(db_path)
    try:
        # Insert payment
        cursor = conn.execute(
            "INSERT INTO debt_payments (debt_id, date, amount, note) VALUES (?, ?, ?, ?)",
            (debt_id, date, amount, note)
        )

        # Update pending balance
        conn.execute(
            "UPDATE debts SET pending_balance = pending_balance - ? WHERE id = ?",
            (amount, debt_id)
        )

        # Check if debt is fully paid
        debt = conn.execute(
            "SELECT pending_balance FROM debts WHERE id = ?", (debt_id,)
        ).fetchone()

        if debt and debt["pending_balance"] <= 0:
            conn.execute(
                "UPDATE debts SET status = 'paid' WHERE id = ?", (debt_id,)
            )

        conn.commit()
        return {"id": cursor.lastrowid, "message": "Debt payment recorded successfully"}
    except sqlite3.Error as e:
        conn.rollback()
        raise e
    finally:
        conn.close()


# ============================================================
# MONTHLY PAYMENTS (MSI)
# ============================================================

def get_monthly_payments(db_path: str, account_id: Optional[int] = None) -> list[dict]:
    """Get monthly payments, optionally filtered by account."""
    conn = get_connection(db_path)
    try:
        query = """SELECT mp.*, a.name as account_name
                   FROM monthly_payments mp
                   LEFT JOIN accounts a ON mp.account_id = a.id"""
        params = []
        if account_id:
            query += " WHERE mp.account_id = ?"
            params.append(account_id)
        query += " ORDER BY mp.remaining_months"
        rows = conn.execute(query, params).fetchall()
        return [dict_from_row(r) for r in rows]
    finally:
        conn.close()


def create_monthly_payment(db_path: str, account_id: int, description: str,
                           total_amount: float, total_months: int,
                           remaining_months: int, monthly_payment: float,
                           start_date: Optional[str] = None,
                           end_date: Optional[str] = None,
                           note: Optional[str] = None) -> dict:
    """Create a new monthly payment record."""
    conn = get_connection(db_path)
    try:
        cursor = conn.execute(
            """INSERT INTO monthly_payments (account_id, description, total_amount,
               total_months, remaining_months, monthly_payment, start_date, end_date, note)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (account_id, description, total_amount, total_months,
             remaining_months, monthly_payment, start_date, end_date, note)
        )
        conn.commit()
        return {"id": cursor.lastrowid, "message": "Monthly payment created successfully"}
    except sqlite3.Error as e:
        conn.rollback()
        raise e
    finally:
        conn.close()


# ============================================================
# FIXED EXPENSES
# ============================================================

def get_fixed_expenses(db_path: str, active_only: bool = True) -> list[dict]:
    """Get fixed expenses."""
    conn = get_connection(db_path)
    try:
        query = """SELECT fe.*, c.name as category_name
                   FROM fixed_expenses fe
                   LEFT JOIN categories c ON fe.category_id = c.id"""
        if active_only:
            query += " WHERE fe.active = 1"
        query += " ORDER BY fe.description"
        rows = conn.execute(query).fetchall()
        return [dict_from_row(r) for r in rows]
    finally:
        conn.close()


def create_fixed_expense(db_path: str, description: str, amount: float,
                         category_id: Optional[int] = None,
                         account_id: Optional[int] = None,
                         payment_day: Optional[int] = None,
                         active: int = 1, notes: Optional[str] = None) -> dict:
    """Create a new fixed expense."""
    conn = get_connection(db_path)
    try:
        cursor = conn.execute(
            """INSERT INTO fixed_expenses (description, category_id, account_id,
               amount, payment_day, active, notes)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (description, category_id, account_id, amount, payment_day, active, notes)
        )
        conn.commit()
        return {"id": cursor.lastrowid, "message": f"Fixed expense '{description}' created"}
    except sqlite3.Error as e:
        conn.rollback()
        raise e
    finally:
        conn.close()


# ============================================================
# ACTIVE LOANS (money others owe to user)
# ============================================================

def get_active_loans(db_path: str, status: Optional[str] = None) -> list[dict]:
    """Get active loans."""
    conn = get_connection(db_path)
    try:
        query = "SELECT * FROM active_loans"
        params = []
        if status:
            query += " WHERE status = ?"
            params.append(status)
        query += " ORDER BY priority, pending_balance DESC"
        rows = conn.execute(query, params).fetchall()
        return [dict_from_row(r) for r in rows]
    finally:
        conn.close()


def create_active_loan(db_path: str, person: str, lent_amount: float,
                       pending_balance: float, description: Optional[str] = None,
                       loan_date: Optional[str] = None, due_date: Optional[str] = None,
                       status: str = "active", priority: int = 3,
                       notes: Optional[str] = None) -> dict:
    """Create a new active loan."""
    conn = get_connection(db_path)
    try:
        cursor = conn.execute(
            """INSERT INTO active_loans (person, description, lent_amount, pending_balance,
               loan_date, due_date, status, priority, notes)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (person, description, lent_amount, pending_balance,
             loan_date, due_date, status, priority, notes)
        )
        conn.commit()
        return {"id": cursor.lastrowid, "message": f"Loan to '{person}' created successfully"}
    except sqlite3.Error as e:
        conn.rollback()
        raise e
    finally:
        conn.close()


def create_loan_payment(db_path: str, loan_id: int, date: str,
                        amount: float, note: Optional[str] = None) -> dict:
    """Record a loan payment received."""
    conn = get_connection(db_path)
    try:
        cursor = conn.execute(
            "INSERT INTO loan_payments (loan_id, date, amount, note) VALUES (?, ?, ?, ?)",
            (loan_id, date, amount, note)
        )

        # Update pending balance
        conn.execute(
            "UPDATE active_loans SET pending_balance = pending_balance - ? WHERE id = ?",
            (amount, loan_id)
        )

        # Check if fully paid
        loan = conn.execute(
            "SELECT pending_balance FROM active_loans WHERE id = ?", (loan_id,)
        ).fetchone()

        if loan and loan["pending_balance"] <= 0:
            conn.execute(
                "UPDATE active_loans SET status = 'paid' WHERE id = ?", (loan_id,)
            )

        conn.commit()
        return {"id": cursor.lastrowid, "message": "Loan payment recorded successfully"}
    except sqlite3.Error as e:
        conn.rollback()
        raise e
    finally:
        conn.close()


# ============================================================
# SAVINGS
# ============================================================

def get_savings(db_path: str, account_id: Optional[int] = None,
                active_only: bool = True) -> list[dict]:
    """Get savings goals."""
    conn = get_connection(db_path)
    try:
        query = """SELECT s.*, a.name as account_name, a.bank as account_bank
                   FROM savings s
                   JOIN accounts a ON s.account_id = a.id"""
        params = []
        conditions = []
        if active_only:
            conditions.append("s.active = 1")
        if account_id:
            conditions.append("s.account_id = ?")
            params.append(account_id)
        if conditions:
            query += " WHERE " + " AND ".join(conditions)
        query += " ORDER BY s.name"
        rows = conn.execute(query, params).fetchall()
        return [dict_from_row(r) for r in rows]
    finally:
        conn.close()


def get_savings_by_id(db_path: str, savings_id: int) -> Optional[dict]:
    """Get a single savings goal by ID."""
    conn = get_connection(db_path)
    try:
        row = conn.execute(
            """SELECT s.*, a.name as account_name
               FROM savings s
               JOIN accounts a ON s.account_id = a.id
               WHERE s.id = ?""",
            (savings_id,)
        ).fetchone()
        return dict_from_row(row)
    finally:
        conn.close()


def create_savings(db_path: str, account_id: int, name: str,
                   amount: float = 0, goal: Optional[float] = None,
                   goal_date: Optional[str] = None, active: int = 1,
                   notes: Optional[str] = None) -> dict:
    """Create a new savings goal."""
    conn = get_connection(db_path)
    try:
        cursor = conn.execute(
            """INSERT INTO savings (account_id, name, amount, goal, goal_date, active, notes)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (account_id, name, amount, goal, goal_date, active, notes)
        )
        conn.commit()
        return {"id": cursor.lastrowid, "message": f"Savings goal '{name}' created"}
    except sqlite3.Error as e:
        conn.rollback()
        raise e
    finally:
        conn.close()


def create_savings_movement(db_path: str, savings_id: int, movement_type: str,
                            amount: float, date: str,
                            note: Optional[str] = None) -> dict:
    """Record a savings movement and update balances."""
    conn = get_connection(db_path)
    try:
        # Get savings info
        savings = conn.execute(
            "SELECT * FROM savings WHERE id = ?", (savings_id,)
        ).fetchone()

        if not savings:
            return {"error": "Savings goal not found"}

        account_id = savings["account_id"]

        # Insert movement
        cursor = conn.execute(
            """INSERT INTO savings_movements (savings_id, type, amount, date, note)
               VALUES (?, ?, ?, ?, ?)""",
            (savings_id, movement_type, amount, date, note)
        )

        # Update savings amount
        if movement_type == "deposit":
            conn.execute(
                "UPDATE savings SET amount = amount + ? WHERE id = ?",
                (amount, savings_id)
            )
            # Decrease available balance in account
            conn.execute(
                "UPDATE accounts SET available_balance = available_balance - ? WHERE id = ?",
                (amount, account_id)
            )
        elif movement_type == "withdrawal":
            conn.execute(
                "UPDATE savings SET amount = amount - ? WHERE id = ?",
                (amount, savings_id)
            )
            # Increase available balance in account
            conn.execute(
                "UPDATE accounts SET available_balance = available_balance + ? WHERE id = ?",
                (amount, account_id)
            )

        conn.commit()
        return {"id": cursor.lastrowid, "message": f"{'Deposit' if movement_type == 'deposit' else 'Withdrawal'} recorded successfully"}
    except sqlite3.Error as e:
        conn.rollback()
        raise e
    finally:
        conn.close()


def get_savings_movements(db_path: str, savings_id: int,
                          limit: int = 50) -> list[dict]:
    """Get movement history for a savings goal."""
    conn = get_connection(db_path)
    try:
        rows = conn.execute(
            """SELECT * FROM savings_movements
               WHERE savings_id = ?
               ORDER BY date DESC, id DESC
               LIMIT ?""",
            (savings_id, limit)
        ).fetchall()
        return [dict_from_row(r) for r in rows]
    finally:
        conn.close()


# ============================================================
# BUDGETS
# ============================================================

def get_budgets(db_path: str, month: Optional[str] = None) -> list[dict]:
    """Get budgets, optionally filtered by month."""
    conn = get_connection(db_path)
    try:
        query = """SELECT b.*, c.name as category_name, c.icon as category_icon
                   FROM budgets b
                   LEFT JOIN categories c ON b.category_id = c.id"""
        params = []
        if month:
            query += " WHERE b.month = ?"
            params.append(month)
        query += " ORDER BY b.month DESC, c.name"
        rows = conn.execute(query, params).fetchall()
        return [dict_from_row(r) for r in rows]
    finally:
        conn.close()


# ============================================================
# ASSETS
# ============================================================

def get_assets(db_path: str, category: Optional[str] = None) -> list[dict]:
    """Get assets, optionally filtered by category."""
    conn = get_connection(db_path)
    try:
        query = "SELECT * FROM assets"
        params = []
        if category:
            query += " WHERE category = ?"
            params.append(category)
        query += " ORDER BY purchase_date DESC"
        rows = conn.execute(query, params).fetchall()
        return [dict_from_row(r) for r in rows]
    finally:
        conn.close()


def get_assets_summary(db_path: str) -> dict:
    """Get total value and count of assets."""
    conn = get_connection(db_path)
    try:
        row = conn.execute(
            "SELECT COUNT(*) as count, COALESCE(SUM(price), 0) as total_value FROM assets"
        ).fetchone()
        return dict_from_row(row)
    finally:
        conn.close()


# ============================================================
# QUERY HELPERS
# ============================================================

def get_account_summary(db_path: str) -> dict:
    """Get a summary of all accounts."""
    conn = get_connection(db_path)
    try:
        accounts = conn.execute(
            """SELECT type,
                      COUNT(*) as count,
                      SUM(balance) as total_balance
               FROM accounts
               WHERE active = 1
               GROUP BY type"""
        ).fetchall()

        total_debts = conn.execute(
            "SELECT COALESCE(SUM(pending_balance), 0) as total FROM debts WHERE status = 'active'"
        ).fetchone()["total"]

        total_savings = conn.execute(
            "SELECT COALESCE(SUM(amount), 0) as total FROM savings WHERE active = 1"
        ).fetchone()["total"]

        return {
            "accounts": [dict_from_row(r) for r in accounts],
            "total_debts": total_debts,
            "total_savings": total_savings
        }
    finally:
        conn.close()


def get_monthly_summary(db_path: str, year: int, month: int) -> dict:
    """Get income/expense summary for a specific month."""
    conn = get_connection(db_path)
    try:
        date_prefix = f"{year:04d}-{month:02d}"

        income = conn.execute(
            """SELECT COALESCE(SUM(amount), 0) as total
               FROM transactions
               WHERE type = 'income' AND date LIKE ?""",
            (f"{date_prefix}%",)
        ).fetchone()["total"]

        expenses = conn.execute(
            """SELECT COALESCE(SUM(amount), 0) as total
               FROM transactions
               WHERE type = 'expense' AND date LIKE ?""",
            (f"{date_prefix}%",)
        ).fetchone()["total"]

        by_category = conn.execute(
            """SELECT c.name, c.icon, SUM(t.amount) as total
               FROM transactions t
               LEFT JOIN categories c ON t.category_id = c.id
               WHERE t.type = 'expense' AND t.date LIKE ?
               GROUP BY t.category_id
               ORDER BY total DESC""",
            (f"{date_prefix}%",)
        ).fetchall()

        return {
            "year": year,
            "month": month,
            "income": income,
            "expenses": expenses,
            "net": income - expenses,
            "by_category": [dict_from_row(r) for r in by_category]
        }
    finally:
        conn.close()
