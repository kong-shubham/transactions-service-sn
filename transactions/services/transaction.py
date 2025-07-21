# transactions/services/transaction.py
"""
Transaction service module for business logic related to financial transactions.
"""
from datetime import datetime, timezone
from typing import Dict, List, Optional
from uuid import uuid4

from transactions.api.models import Transaction
from transactions.clients.accounts_client import accounts_client


class TransactionService:
    """Service for handling transaction operations"""

    def __init__(self) -> None:
        """Initialize the transaction service with empty transaction database."""
        self._transactions_db: Dict[str, List[Transaction]] = {}

    async def get_transactions(self, account_id: str) -> List[Transaction]:
        """Returns a list of all transactions for an account."""
        return self._transactions_db.get(account_id, [])

    async def account_exists(self, account_id: str) -> bool:
        """Check if an account exists in the accounts service."""
        account = await accounts_client.get_account(account_id)
        return account is not None

    async def get_balance(self, account_id: str) -> Optional[float]:
        """Get the current balance for an account from the accounts service."""
        account = await accounts_client.get_account(account_id)
        if account:
            return account.get("balance")
        return None

    async def create_transaction(
        self, account_id: str, amount: float, description: str, transaction_type: str
    ) -> Transaction:
        """
        Create a new transaction for an account.
        Updates the account balance via the accounts service.
        For credits, amount is positive. For debits, amount is recorded as negative.
        """
        if transaction_type == "debit":
            # Debit the account - this will raise an exception if insufficient funds
            await accounts_client.debit_account(account_id, amount)
            # Record amount as negative for debits
            tx_amount = -amount
        else:  # credit
            # Credit the account
            await accounts_client.credit_account(account_id, amount)
            # Record amount as positive for credits
            tx_amount = amount

        # Create the transaction
        transaction = Transaction(
            transaction_id=f"tx-{uuid4().hex[:10]}",
            date=datetime.now(timezone.utc),
            amount=tx_amount,
            description=description,
            transaction_type=transaction_type,
        )

        # Store the transaction
        if account_id not in self._transactions_db:
            self._transactions_db[account_id] = []
        self._transactions_db[account_id].append(transaction)

        return transaction

    async def seed_test_account(self, account_id: str, initial_balance: float):
        """
        This method is now only for testing purposes.
        In production, accounts would be created via the accounts service API.
        """
        # This is a no-op in the actual implementation,
        # since accounts are managed by the accounts service
        # Initialize the transactions list for the account
        if account_id not in self._transactions_db:
            self._transactions_db[account_id] = []

    async def check_account_service_health(self) -> bool:
        """Check if the account service is healthy."""
        return await accounts_client.check_health()


# Create a singleton instance of the transaction service
transaction_service = TransactionService()
