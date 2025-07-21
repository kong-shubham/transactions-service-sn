"""
Tests for the Transaction Service logic.
"""

from unittest.mock import AsyncMock, patch

import pytest

from transactions.services.transaction import TransactionService


@pytest.fixture
async def transaction_service():
    """Create a fresh transaction service for testing"""
    with patch("transactions.services.transaction.accounts_client") as mock_client:
        # Configure default mock behavior
        mock_client.get_account = AsyncMock()
        mock_client.debit_account = AsyncMock()
        mock_client.credit_account = AsyncMock()
        mock_client.check_health = AsyncMock(return_value=True)

        service = TransactionService()
        yield service, mock_client


@pytest.mark.asyncio
async def test_account_exists(transaction_service):
    """Test checking if an account exists"""
    service, mock_client = transaction_service
    account_id = "test-account"

    # Configure mock for non-existent account
    mock_client.get_account.return_value = None

    # Account should not exist initially
    assert await service.account_exists(account_id) is False
    mock_client.get_account.assert_called_once_with(account_id)

    # Reset the mock
    mock_client.get_account.reset_mock()

    # Configure mock for existing account
    mock_client.get_account.return_value = {"account_id": account_id, "balance": 100.00}

    # Now it should exist
    assert await service.account_exists(account_id) is True
    mock_client.get_account.assert_called_once_with(account_id)


@pytest.mark.asyncio
async def test_get_balance(transaction_service):
    """Test getting account balance"""
    service, mock_client = transaction_service
    account_id = "test-account"

    # Configure mock for non-existent account
    mock_client.get_account.return_value = None

    # Balance should be None for non-existent account
    assert await service.get_balance(account_id) is None
    mock_client.get_account.assert_called_once_with(account_id)

    # Reset the mock
    mock_client.get_account.reset_mock()

    # Configure mock for existing account
    mock_client.get_account.return_value = {"account_id": account_id, "balance": 250.00}

    # Balance should be correct
    assert await service.get_balance(account_id) == 250.00
    mock_client.get_account.assert_called_once_with(account_id)


@pytest.mark.asyncio
async def test_get_transactions_empty(transaction_service):
    """Test getting transactions for an account with no transactions"""
    service, mock_client = transaction_service
    account_id = "test-account"

    # Should return empty list for any account (whether it exists or not)
    transactions = await service.get_transactions(account_id)
    assert transactions == []

    # Verify no calls to accounts service (transactions are stored locally)
    mock_client.get_account.assert_not_called()


@pytest.mark.asyncio
async def test_create_credit_transaction(transaction_service):
    """Test creating a credit transaction"""
    service, mock_client = transaction_service
    account_id = "test-account"

    # Configure mock for account check and credit operation
    mock_client.get_account.return_value = {
        "account_id": account_id,
        "balance": 1000.00,
    }
    mock_client.credit_account.return_value = {
        "account_id": account_id,
        "balance": 1200.00,
    }

    # Create credit transaction
    transaction = await service.create_transaction(
        account_id=account_id,
        amount=200.00,
        description="Test Credit",
        transaction_type="credit",
    )

    # Verify transaction details
    assert transaction.amount == 200.00
    assert transaction.description == "Test Credit"
    assert transaction.transaction_type == "credit"
    assert transaction.transaction_id.startswith("tx-")

    # Verify account service calls
    mock_client.credit_account.assert_called_once_with(account_id, 200.00)

    # Verify transaction was stored locally
    transactions = await service.get_transactions(account_id)
    assert len(transactions) == 1
    assert transactions[0].amount == 200.00


@pytest.mark.asyncio
async def test_create_debit_transaction(transaction_service):
    """Test creating a debit transaction"""
    service, mock_client = transaction_service
    account_id = "test-account"

    # Configure mock for account check and debit operation
    mock_client.get_account.return_value = {
        "account_id": account_id,
        "balance": 1000.00,
    }
    mock_client.debit_account.return_value = {
        "account_id": account_id,
        "balance": 850.00,
    }

    # Create debit transaction
    transaction = await service.create_transaction(
        account_id=account_id,
        amount=150.00,
        description="Test Debit",
        transaction_type="debit",
    )

    # Verify transaction details
    assert transaction.amount == -150.00  # Should be negative for debits
    assert transaction.description == "Test Debit"
    assert transaction.transaction_type == "debit"

    # Verify account service calls
    mock_client.debit_account.assert_called_once_with(account_id, 150.00)

    # Verify transaction was stored locally
    transactions = await service.get_transactions(account_id)
    assert len(transactions) == 1
    assert transactions[0].amount == -150.00


@pytest.mark.asyncio
async def test_create_multiple_transactions(transaction_service):
    """Test creating multiple transactions"""
    service, mock_client = transaction_service
    account_id = "test-account"

    # Configure mock for credit/debit operations
    mock_client.get_account.return_value = {
        "account_id": account_id,
        "balance": 1000.00,
    }

    # Mock responses for each transaction
    credit1_response = {"account_id": account_id, "balance": 1500.00}
    debit1_response = {"account_id": account_id, "balance": 1300.00}
    credit2_response = {"account_id": account_id, "balance": 1600.00}

    mock_client.credit_account.side_effect = [credit1_response, credit2_response]
    mock_client.debit_account.return_value = debit1_response

    # Create credit transaction
    await service.create_transaction(
        account_id=account_id,
        amount=500.00,
        description="Credit 1",
        transaction_type="credit",
    )

    # Create debit transaction
    await service.create_transaction(
        account_id=account_id,
        amount=200.00,
        description="Debit 1",
        transaction_type="debit",
    )

    # Create another credit transaction
    await service.create_transaction(
        account_id=account_id,
        amount=300.00,
        description="Credit 2",
        transaction_type="credit",
    )

    # Verify account service calls
    assert mock_client.credit_account.call_count == 2
    assert mock_client.debit_account.call_count == 1

    # First credit call
    mock_client.credit_account.assert_any_call(account_id, 500.00)
    # Debit call
    mock_client.debit_account.assert_called_once_with(account_id, 200.00)
    # Second credit call
    mock_client.credit_account.assert_any_call(account_id, 300.00)

    # Verify all transactions were stored locally
    transactions = await service.get_transactions(account_id)
    assert len(transactions) == 3

    # Verify specific transactions exist
    descriptions = [tx.description for tx in transactions]
    assert "Credit 1" in descriptions
    assert "Debit 1" in descriptions
    assert "Credit 2" in descriptions

    # Verify transaction amounts
    assert any(tx.amount == 500.00 for tx in transactions)
    assert any(tx.amount == -200.00 for tx in transactions)
    assert any(tx.amount == 300.00 for tx in transactions)


@pytest.mark.asyncio
async def test_insufficient_funds(transaction_service):
    """Test insufficient funds error"""
    service, mock_client = transaction_service
    account_id = "test-account"

    # Configure mock for account check
    mock_client.get_account.return_value = {
        "account_id": account_id,
        "balance": 1000.00,
    }

    # Configure mock to raise ValueError for insufficient funds
    # from fastapi import HTTPException, status

    def insufficient_funds(*args, **kwargs):
        raise ValueError("Insufficient funds")

    mock_client.debit_account.side_effect = insufficient_funds

    # Try to debit more than the balance
    with pytest.raises(ValueError) as excinfo:
        await service.create_transaction(
            account_id=account_id,
            amount=1100.00,
            description="Excessive Debit",
            transaction_type="debit",
        )

    assert "Insufficient funds" in str(excinfo.value)

    # Verify debit was attempted
    mock_client.debit_account.assert_called_once_with(account_id, 1100.00)

    # Verify no transaction was recorded locally
    transactions = await service.get_transactions(account_id)
    assert len(transactions) == 0


@pytest.mark.asyncio
async def test_check_account_service_health(transaction_service):
    """Test checking account service health"""
    service, mock_client = transaction_service

    # Configure mock for healthy service
    mock_client.check_health.return_value = True
    assert await service.check_account_service_health() is True

    # Configure mock for unhealthy service
    mock_client.check_health.return_value = False
    assert await service.check_account_service_health() is False


@pytest.mark.asyncio
async def test_seed_test_account(transaction_service):
    """Test that seed_test_account only initializes transaction storage"""
    service, mock_client = transaction_service
    account_id = "test-account"

    # Seed test account
    await service.seed_test_account(account_id, 500.00)

    # Verify no calls to account service (since we're just initializing local storage)
    mock_client.get_account.assert_not_called()
    mock_client.credit_account.assert_not_called()

    # Verify get_transactions returns empty list for the seeded account
    transactions = await service.get_transactions(account_id)
    assert transactions == []
