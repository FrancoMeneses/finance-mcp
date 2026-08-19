# Finance MCP

Personal finance management via Model Context Protocol (MCP).

## Overview

This MCP server provides tools for managing personal finances:
- **Accounts**: Bank accounts, credit cards, savings
- **Transactions**: Income, expenses, transfers
- **Debts**: Track debts and payments
- **Monthly Payments**: Installments (MSI) tracking
- **Fixed Expenses**: Recurring monthly expenses
- **Active Loans**: Money others owe to you
- **Savings**: Goals and movement tracking
- **Budgets**: Monthly budget limits
- **Assets**: Personal asset inventory

## Installation

```bash
# Clone the repository
git clone https://github.com/FrancoMeneses/finance-mcp.git
cd finance-mcp

# Install dependencies
pip install -r requirements.txt

# Initialize the database (optional - server creates it on first run)
sqlite3 finance.db < schema/init.sql
```

## Usage

### With Hermes Agent

Add to `~/.hermes/config.yaml`:

```yaml
mcp_servers:
  finance:
    command: "python3"
    args: ["/path/to/finance-mcp/src/finance/server.py"]
    env:
      DB_PATH: "/path/to/finance.db"
```

### Standalone

```bash
# Set database path
export DB_PATH="/path/to/finance.db"

# Run the server
python src/finance/server.py
```

## Available Tools

### Accounts
- `list_accounts` - List all accounts
- `get_account` - Get account details
- `create_new_account` - Create a new account
- `update_account_balance` - Update account balance

### Categories
- `list_categories` - List all categories
- `get_category` - Get category details

### Transactions
- `list_transactions` - List transactions with filters
- `add_transaction` - Record a new transaction

### Debts
- `list_debts` - List debts
- `get_debt` - Get debt details
- `add_debt` - Register a new debt
- `record_debt_payment` - Record a debt payment

### Monthly Payments (MSI)
- `list_monthly_payments` - List installments
- `add_monthly_payment` - Register new installment

### Fixed Expenses
- `list_fixed_expenses` - List fixed expenses
- `add_fixed_expense` - Add fixed expense

### Active Loans
- `list_active_loans` - List loans given to others
- `add_active_loan` - Register a new loan
- `record_loan_payment` - Record payment received

### Savings
- `list_savings` - List savings goals
- `get_savings_goal` - Get savings goal details
- `add_savings_goal` - Create savings goal
- `record_savings_movement` - Deposit/withdraw from savings
- `list_savings_movements` - View savings history

### Budgets
- `list_budgets` - List budgets

### Assets
- `list_assets` - List personal assets
- `get_assets_total` - Get total asset value

### Summaries
- `get_account_overview` - Quick account summary
- `get_monthly_report` - Monthly income/expense report

## Database Schema

See `schema/init.sql` for the complete database schema.

## Project Structure

```
finance-mcp/
├── README.md
├── requirements.txt
├── schema/
│   └── init.sql         # Database schema
├── src/
│   └── finance/
│       ├── __init__.py
│       ├── server.py    # MCP server (FastMCP)
│       ├── db.py        # Database access layer
│       └── models.py    # Pydantic validation models
├── tests/
│   └── ...
└── docs/
    └── architecture.md
```

## License

MIT
