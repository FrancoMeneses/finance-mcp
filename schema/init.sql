-- ============================================================
-- Finanzas MCP - Database Schema
-- Personal finance management via Model Context Protocol
-- ============================================================

-- Enable foreign keys
PRAGMA foreign_keys = ON;

-- ============================================================
-- ACCOUNTS
-- Bank accounts, credit cards, savings
-- ============================================================
CREATE TABLE IF NOT EXISTS accounts (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    name            TEXT NOT NULL,                           -- "Debit MP", "Credit BBVA"
    bank            TEXT NOT NULL,                           -- "MercadoPago", "BBVA"
    type            TEXT NOT NULL CHECK(type IN ('debit', 'credit', 'savings')),
    balance         REAL NOT NULL DEFAULT 0,                 -- Total balance
    available_balance REAL,                                  -- Available (total - savings)
    credit_limit    REAL,                                    -- Credit limit (credit cards)
    statement_day   INTEGER,                                 -- Statement day (credit cards)
    payment_day     INTEGER,                                 -- Payment day (credit cards)
    interest_rate   REAL,                                    -- Annual interest rate
    notes           TEXT,
    active          INTEGER NOT NULL DEFAULT 1,
    current_payment REAL,                                    -- Current month payment
    created_at      TEXT DEFAULT (datetime('now'))
);

-- ============================================================
-- CATEGORIES
-- Expense/income categories (hierarchical)
-- ============================================================
CREATE TABLE IF NOT EXISTS categories (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    name            TEXT NOT NULL,                           -- "Food", "Transport"
    level           INTEGER DEFAULT 0,                       -- 0=root, 1=subcategory
    parent_id       INTEGER REFERENCES categories(id),
    icon            TEXT DEFAULT '📦',
    monthly_budget  REAL                                     -- Monthly budget limit
);

-- ============================================================
-- TRANSACTIONS
-- Income, expenses, transfers between accounts
-- ============================================================
CREATE TABLE IF NOT EXISTS transactions (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    date            TEXT NOT NULL,                           -- YYYY-MM-DD
    type            TEXT NOT NULL CHECK(type IN ('income', 'expense', 'transfer')),
    amount          REAL NOT NULL,
    category_id     INTEGER REFERENCES categories(id),
    description     TEXT,
    method          TEXT,                                    -- "cash", "card", "transfer"
    tags            TEXT,                                    -- Comma-separated: "gasoline,moto"
    account_id      INTEGER REFERENCES accounts(id),         -- Source account
    account_dest_id INTEGER REFERENCES accounts(id),         -- Destination (transfers)
    created_at      TEXT DEFAULT (datetime('now'))
);

-- ============================================================
-- DEBTS
-- Money the user owes (credit cards, loans, etc.)
-- ============================================================
CREATE TABLE IF NOT EXISTS debts (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    creditor        TEXT NOT NULL,                           -- "BBVA", "Nu", "CNC"
    description     TEXT,
    original_amount REAL NOT NULL,
    pending_balance REAL NOT NULL,
    interest_rate   REAL,
    due_date        TEXT,                                    -- YYYY-MM-DD
    status          TEXT DEFAULT 'active' CHECK(status IN ('active', 'paid')),
    priority        INTEGER DEFAULT 3                        -- 1=high, 2=medium, 3=low
);

-- ============================================================
-- DEBT_PAYMENTS
-- Payment history for debts
-- ============================================================
CREATE TABLE IF NOT EXISTS debt_payments (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    debt_id     INTEGER REFERENCES debts(id),
    date        TEXT NOT NULL,                               -- YYYY-MM-DD
    amount      REAL NOT NULL,
    note        TEXT
);

-- ============================================================
-- MONTHLY_PAYMENTS
-- Installment purchases (MSI) and term loans
-- ============================================================
CREATE TABLE IF NOT EXISTS monthly_payments (
    id                INTEGER PRIMARY KEY AUTOINCREMENT,
    account_id        INTEGER REFERENCES accounts(id),
    description       TEXT NOT NULL,                         -- "MSI BBVA - 6 months"
    total_amount      REAL NOT NULL,
    total_months      INTEGER NOT NULL,
    remaining_months  INTEGER NOT NULL,
    monthly_payment   REAL NOT NULL,
    start_date        TEXT,
    end_date          TEXT,
    note              TEXT,
    created_at        TEXT DEFAULT (datetime('now'))
);

-- ============================================================
-- FIXED_EXPENSES
-- Recurring monthly expenses (reference only, not auto-deducted)
-- ============================================================
CREATE TABLE IF NOT EXISTS fixed_expenses (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    description   TEXT NOT NULL,                             -- "Internet", "Gasoline"
    category_id   INTEGER REFERENCES categories(id),
    account_id    INTEGER REFERENCES accounts(id),
    amount        REAL NOT NULL,
    payment_day   INTEGER,
    active        INTEGER NOT NULL DEFAULT 1,
    notes         TEXT,
    created_at    TEXT DEFAULT (datetime('now'))
);

-- ============================================================
-- ACTIVE_LOANS
-- Money others owe to the user
-- ============================================================
CREATE TABLE IF NOT EXISTS active_loans (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    person          TEXT NOT NULL,                           -- "Hugo"
    description     TEXT,
    lent_amount     REAL NOT NULL,
    pending_balance REAL NOT NULL,
    loan_date       TEXT,
    due_date        TEXT,
    status          TEXT DEFAULT 'active' CHECK(status IN ('active', 'paid', 'partial')),
    priority        INTEGER DEFAULT 3,
    notes           TEXT,
    created_at      TEXT DEFAULT (datetime('now'))
);

-- ============================================================
-- LOAN_PAYMENTS
-- Payment history for active loans
-- ============================================================
CREATE TABLE IF NOT EXISTS loan_payments (
    id        INTEGER PRIMARY KEY AUTOINCREMENT,
    loan_id   INTEGER REFERENCES active_loans(id),
    date      TEXT NOT NULL,                                 -- YYYY-MM-DD
    amount    REAL NOT NULL,
    note      TEXT
);

-- ============================================================
-- SAVINGS
-- Savings goals within accounts
-- ============================================================
CREATE TABLE IF NOT EXISTS savings (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    account_id    INTEGER NOT NULL REFERENCES accounts(id),  -- Where the money is
    name          TEXT NOT NULL,                             -- "Chetumal Trip", "450 MT"
    amount        REAL DEFAULT 0,                            -- Current saved amount
    goal          REAL,                                      -- Target amount (optional)
    goal_date     TEXT,                                      -- Target date (optional)
    active        INTEGER NOT NULL DEFAULT 1,
    notes         TEXT,
    created_at    TEXT DEFAULT (datetime('now'))
);

-- ============================================================
-- SAVINGS_MOVEMENTS
-- Deposit/withdrawal history for savings
-- ============================================================
CREATE TABLE IF NOT EXISTS savings_movements (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    savings_id  INTEGER NOT NULL REFERENCES savings(id),
    type        TEXT NOT NULL CHECK(type IN ('deposit', 'withdrawal')),
    amount      REAL NOT NULL,
    date        TEXT NOT NULL,                               -- YYYY-MM-DD
    note        TEXT,
    created_at  TEXT DEFAULT (datetime('now'))
);

-- ============================================================
-- BUDGETS
-- Monthly budget limits by category
-- ============================================================
CREATE TABLE IF NOT EXISTS budgets (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    category_id   INTEGER REFERENCES categories(id),
    month         TEXT NOT NULL,                             -- YYYY-MM
    limit_amount  REAL NOT NULL
);

-- ============================================================
-- ASSETS
-- Personal assets / net worth inventory
-- ============================================================
CREATE TABLE IF NOT EXISTS assets (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    purchase_date   TEXT NOT NULL,                           -- YYYY-MM-DD
    item            TEXT NOT NULL,                           -- "Macbook Air M1"
    price           REAL NOT NULL,                           -- Purchase price
    category        TEXT,                                    -- "Computing", "Moto"
    where_bought    TEXT,
    notes           TEXT,
    created_at      TEXT DEFAULT (datetime('now'))
);

-- ============================================================
-- INDEXES
-- ============================================================
CREATE INDEX IF NOT EXISTS idx_transactions_date ON transactions(date);
CREATE INDEX IF NOT EXISTS idx_transactions_type ON transactions(type);
CREATE INDEX IF NOT EXISTS idx_transactions_account ON transactions(account_id);
CREATE INDEX IF NOT EXISTS idx_debts_status ON debts(status);
CREATE INDEX IF NOT EXISTS idx_savings_account ON savings(account_id);
CREATE INDEX IF NOT EXISTS idx_savings_movements_savings ON savings_movements(savings_id);
CREATE INDEX IF NOT EXISTS idx_monthly_payments_account ON monthly_payments(account_id);
