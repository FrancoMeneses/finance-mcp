# Architecture

## Overview

Finance MCP is a Model Context Protocol server for personal finance management. It provides structured tools for managing accounts, transactions, debts, savings, and more.

## Design Principles

1. **Separation of Concerns**: Clear layers between MCP interface, business logic, and data access
2. **Data Integrity**: All operations validated before database writes
3. **Immutability**: Transactions are append-only; balances computed from history
4. **Single Source of Truth**: Database is the authoritative state; no cached copies

## Layers

```
┌─────────────────────────────────────────┐
│            MCP Client (Hermes)          │
└─────────────────────────────────────────┘
                    │
                    ▼
┌─────────────────────────────────────────┐
│           server.py (FastMCP)           │
│  - Tool definitions                     │
│  - Parameter validation (Pydantic)      │
│  - Logging                              │
└─────────────────────────────────────────┘
                    │
                    ▼
┌─────────────────────────────────────────┐
│              db.py (Data Layer)         │
│  - SQL queries (parameterized)          │
│  - Transaction management               │
│  - Balance updates                      │
└─────────────────────────────────────────┘
                    │
                    ▼
┌─────────────────────────────────────────┐
│           SQLite Database               │
│  - accounts, transactions, debts, etc.  │
│  - Foreign key constraints              │
│  - Indexes for performance              │
└─────────────────────────────────────────┘
```

## Data Flow

### Recording an Expense
```
User: "Add $500 expense for food"
    │
    ▼
server.py: add_transaction(type="expense", amount=500, ...)
    │
    ▼
models.py: Validates request (amount > 0, date format, etc.)
    │
    ▼
db.py: create_transaction()
    ├── INSERT INTO transactions
    └── UPDATE accounts SET balance = balance - 500
    │
    ▼
Returns: {"id": 123, "message": "Transaction created"}
```

### Savings Movement
```
User: "Deposit $2000 to Chetumal Trip savings"
    │
    ▼
server.py: record_savings_movement(savings_id=1, type="deposit", amount=2000, ...)
    │
    ▼
db.py: create_savings_movement()
    ├── INSERT INTO savings_movements
    ├── UPDATE savings SET amount = amount + 2000
    └── UPDATE accounts SET available_balance = available_balance - 2000
    │
    ▼
Returns: {"id": 456, "message": "Deposit recorded"}
```

## Error Handling

All tools return a consistent response format:

```python
{
    "success": True/False,
    "data": {...},      # On success
    "error": "...",     # On failure
    "message": "..."    # Human-readable message
}
```

Database operations use transactions:
1. Start transaction
2. Execute operations
3. Commit on success
4. Rollback on error

## Security Considerations

- All SQL queries use parameterized statements (no string concatenation)
- Database path configurable via environment variable
- No sensitive data in logs (amounts are logged, not card numbers)
- Foreign key constraints enforced
