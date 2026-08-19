"""Tests for database operations."""

import pytest
from src.finanzas.db import (
    get_accounts, create_account, get_account_by_id,
    get_categories,
    create_transaction, get_transactions,
    get_debts, create_debt, create_debt_payment,
    create_savings, create_savings_movement, get_savings,
    get_account_summary, get_monthly_summary,
)


class TestAccounts:
    def test_get_accounts_empty(self, temp_db):
        result = get_accounts(temp_db)
        assert result == []

    def test_create_and_get_account(self, temp_db):
        result = create_account(temp_db, "Test Account", "TestBank", "debit", 1000)
        assert "id" in result

        account = get_account_by_id(temp_db, result["id"])
        assert account["name"] == "Test Account"
        assert account["balance"] == 1000

    def test_get_accounts_with_data(self, sample_data):
        accounts = get_accounts(sample_data)
        assert len(accounts) == 3


class TestTransactions:
    def test_create_expense(self, sample_data):
        result = create_transaction(
            sample_data, "2026-08-18", "expense", 500,
            description="Test expense", account_id=1
        )
        assert "id" in result

        # Check balance was updated
        account = get_account_by_id(sample_data, 1)
        assert account["balance"] == 14500  # 15000 - 500

    def test_create_income(self, sample_data):
        result = create_transaction(
            sample_data, "2026-08-18", "income", 5000,
            description="Test income", account_id=1
        )
        assert "id" in result

        account = get_account_by_id(sample_data, 1)
        assert account["balance"] == 20000  # 15000 + 5000

    def test_create_transfer(self, sample_data):
        result = create_transaction(
            sample_data, "2026-08-18", "transfer", 1000,
            description="Test transfer", account_id=1, account_dest_id=2
        )
        assert "id" in result

        account1 = get_account_by_id(sample_data, 1)
        account2 = get_account_by_id(sample_data, 2)
        assert account1["balance"] == 14000  # 15000 - 1000
        assert account2["balance"] == 6000   # 5000 + 1000


class TestDebts:
    def test_create_debt(self, temp_db):
        result = create_debt(temp_db, "Test Bank", 10000, 10000)
        assert "id" in result

        debts = get_debts(temp_db)
        assert len(debts) == 1
        assert debts[0]["creditor"] == "Test Bank"

    def test_debt_payment(self, temp_db):
        debt = create_debt(temp_db, "Test Bank", 10000, 10000)
        payment = create_debt_payment(temp_db, debt["id"], "2026-08-18", 2000)
        assert "id" in payment

        updated_debt = get_debts(temp_db)[0]
        assert updated_debt["pending_balance"] == 8000


class TestSavings:
    def test_create_savings(self, sample_data):
        result = create_savings(sample_data, 1, "Trip Fund", 5000, goal=10000)
        assert "id" in result

        savings = get_savings(sample_data)
        assert len(savings) == 1
        assert savings[0]["name"] == "Trip Fund"

    def test_savings_deposit(self, sample_data):
        savings = create_savings(sample_data, 1, "Trip Fund", 0)
        movement = create_savings_movement(
            sample_data, savings["id"], "deposit", 2000, "2026-08-18"
        )
        assert "id" in movement

        updated = get_savings(sample_data)[0]
        assert updated["amount"] == 2000

    def test_savings_withdrawal(self, sample_data):
        savings = create_savings(sample_data, 1, "Trip Fund", 5000)
        movement = create_savings_movement(
            sample_data, savings["id"], "withdrawal", 1000, "2026-08-18"
        )
        assert "id" in movement

        updated = get_savings(sample_data)[0]
        assert updated["amount"] == 4000


class TestSummaries:
    def test_account_summary(self, sample_data):
        summary = get_account_summary(sample_data)
        assert "accounts" in summary
        assert "total_savings" in summary
