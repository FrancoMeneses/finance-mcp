"""Test fixtures for Finance MCP."""

import pytest
import sqlite3
import tempfile
from pathlib import Path


@pytest.fixture
def temp_db():
    """Create a temporary test database."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = f.name

    # Initialize schema
    schema_path = Path(__file__).parent.parent / "schema" / "init.sql"
    if schema_path.exists():
        conn = sqlite3.connect(db_path)
        conn.executescript(schema_path.read_text())
        conn.close()

    yield db_path

    # Cleanup
    Path(db_path).unlink(missing_ok=True)


@pytest.fixture
def sample_data(temp_db):
    """Insert sample data for testing."""
    conn = sqlite3.connect(temp_db)

    # Sample accounts
    conn.execute("""
        INSERT INTO accounts (name, bank, type, balance, available_balance, credit_limit, statement_day, payment_day)
        VALUES
            ('Debit MP', 'MercadoPago', 'debit', 15000, 15000, NULL, NULL, NULL),
            ('Credit BBVA', 'BBVA', 'credit', 5000, 500, 11600, 10, 31),
            ('Credit Nu', 'Nu', 'credit', 3000, 22000, 25600, 22, 31)
    """)

    # Sample categories
    conn.execute("""
        INSERT INTO categories (name, level, icon)
        VALUES
            ('Food', 0, '🍔'),
            ('Transport', 0, '🚗'),
            ('Entertainment', 0, '🎮')
    """)

    # Sample debts
    conn.execute("""
        INSERT INTO debts (creditor, description, original_amount, pending_balance, status, priority)
        VALUES ('CNC', 'CNC Loan', 44835, 22417.50, 'active', 2)
    """)

    conn.commit()
    conn.close()

    return temp_db
