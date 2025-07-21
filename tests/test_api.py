"""
Tests for the Transactions API.
"""

import uuid
from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient

from transactions.main import app

# from transactions.api.models import ErrorCode

# TestClient doesn't support async directly, so we need to mock the async functions


@pytest.fixture
def client():
    """Test client fixture"""
    return TestClient(app)


@pytest.fixture
def mock_account_service():
    """Mock the accounts service client"""
    with patch("transactions.services.transaction.accounts_client") as mock_client:
        mock_client.get_account = AsyncMock()
        mock_client.debit_account = AsyncMock()
        mock_client.credit_account = AsyncMock()
        mock_client.check_health = AsyncMock(return_value=True)
        yield mock_client


def test_health_check(client, mock_account_service):
    """Test the health check endpoint"""
    # Configure mock
    mock_account_service.check_health.return_value = True

    # Make request
    response = client.get("/health")

    # Verify response
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "UP"
    assert data["account_service"] == "UP"
    assert data["message"] == "All services operational"

    # Verify mock was called
    mock_account_service.check_health.assert_called_once()


def test_health_check_service_down(client, mock_account_service):
    """Test the health check when account service is down"""
    # Configure mock
    mock_account_service.check_health.return_value = False

    # Make request
    response = client.get("/health")

    # Verify response
    assert response.status_code == 503
    data = response.json()
    assert data["status"] == "UP"
    assert data["account_service"] == "DOWN"
    assert "not available" in data["message"].lower()


def test_get_transactions_nonexistent_account(client, mock_account_service):
    """Test getting transactions for a non-existent account"""
    # Configure mock to simulate account not found
    mock_account_service.get_account.return_value = None

    # Generate a random account ID
    random_id = str(uuid.uuid4())

    # Make request
    response = client.get(f"/accounts/{random_id}/transactions")

    # Verify response
    assert response.status_code == 404
    data = response.json()
    assert data["error_code"] == "NOT_FOUND"

    # Verify mock was called with correct argument
    mock_account_service.get_account.assert_called_once_with(random_id)


def test_create_and_get_transactions(client, mock_account_service):
    """Test creating and then getting transactions"""
    # Set up test account ID
    account_id = str(uuid.uuid4())

    # Configure mocks for account existence and balance updates
    mock_account_service.get_account.return_value = {
        "account_id": account_id,
        "balance": 1000.00,
    }

    # Configure mock for successful debit operation
    mock_account_service.debit_account.return_value = {
        "account_id": account_id,
        "balance": 800.00,
    }

    # Configure mock for successful credit operation
    mock_account_service.credit_account.return_value = {
        "account_id": account_id,
        "balance": 1300.00,
    }

    # Create a credit transaction
    credit_response = client.post(
        f"/accounts/{account_id}/transactions",
        json={
            "amount": 500.00,
            "description": "Test Credit",
            "transaction_type": "credit",
        },
    )

    # Verify credit transaction response
    assert credit_response.status_code == 201
    credit_data = credit_response.json()
    assert credit_data["amount"] == 500.00
    assert credit_data["description"] == "Test Credit"
    assert credit_data["transaction_type"] == "credit"

    # Verify credit mock was called correctly
    mock_account_service.credit_account.assert_called_once_with(account_id, 500.00)

    # Create a debit transaction
    debit_response = client.post(
        f"/accounts/{account_id}/transactions",
        json={
            "amount": 200.00,
            "description": "Test Debit",
            "transaction_type": "debit",
        },
    )

    # Verify debit transaction response
    assert debit_response.status_code == 201
    debit_data = debit_response.json()
    assert debit_data["amount"] == -200.00  # Debits are negative
    assert debit_data["description"] == "Test Debit"
    assert debit_data["transaction_type"] == "debit"

    # Verify debit mock was called correctly
    mock_account_service.debit_account.assert_called_once_with(account_id, 200.00)

    # Get all transactions
    get_response = client.get(f"/accounts/{account_id}/transactions")

    # Verify get response
    assert get_response.status_code == 200
    transactions = get_response.json()
    assert len(transactions) == 2

    # Verify transaction details in the list
    assert any(tx["description"] == "Test Credit" for tx in transactions)
    assert any(tx["description"] == "Test Debit" for tx in transactions)

    # Verify account existence was checked for all operations
    assert mock_account_service.get_account.call_count == 3


def test_insufficient_funds(client, mock_account_service):
    """Test debiting more than available balance"""
    # Set up test account ID
    account_id = str(uuid.uuid4())

    # Configure mocks for account existence check
    mock_account_service.get_account.return_value = {
        "account_id": account_id,
        "balance": 1000.00,
    }

    # Configure mock to simulate insufficient funds error
    _ = {
        "error_code": "INSUFFICIENT_FUNDS",
        "message": "Failed to debit account: Insufficient funds - balance is 1000.00, attempted to debit 2000.00",
    }
    mock_account_service.debit_account.side_effect = Exception("Insufficient funds")

    # Create a special side effect that raises the right HTTPException
    from fastapi import HTTPException, status

    from transactions.api.models import ErrorCode, ErrorResponse

    def insufficient_funds_error(*args, **kwargs):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=ErrorResponse(
                error_code=ErrorCode.INSUFFICIENT_FUNDS,
                message="Insufficient Funds: Account balance too low for requested debit",
            ).model_dump(),  # Changed from .dict() to .model_dump()
        )

    mock_account_service.debit_account.side_effect = insufficient_funds_error

    # Try to debit more than the account balance
    response = client.post(
        f"/accounts/{account_id}/transactions",
        json={
            "amount": 2000.00,  # Account only has 1000.00
            "description": "Excessive Debit",
            "transaction_type": "debit",
        },
    )

    # Verify response
    assert response.status_code == 400
    data = response.json()
    assert data["error_code"] == "INSUFFICIENT_FUNDS"

    # Verify mock calls
    mock_account_service.get_account.assert_called_once_with(account_id)
    mock_account_service.debit_account.assert_called_once_with(account_id, 2000.00)


def test_invalid_decimal_places(client, mock_account_service):
    """Test transaction with too many decimal places"""
    # Set up test account ID
    account_id = str(uuid.uuid4())

    # Configure mock for account existence check
    mock_account_service.get_account.return_value = {
        "account_id": account_id,
        "balance": 1000.00,
    }

    # Make request with invalid decimal places
    response = client.post(
        f"/accounts/{account_id}/transactions",
        json={
            "amount": 100.123,  # More than 2 decimal places
            "description": "Invalid Amount",
            "transaction_type": "credit",
        },
    )

    # Verify response
    assert response.status_code == 400
    data = response.json()
    assert data["error_code"] == "BAD_REQUEST"
    assert "decimal places" in data["message"].lower()

    # Verify account was checked but no credit/debit was attempted
    mock_account_service.get_account.assert_called_once_with(account_id)
    mock_account_service.credit_account.assert_not_called()


def test_non_existent_account_transaction(client, mock_account_service):
    """Test creating transaction for non-existent account"""
    # Configure mock to simulate account not found
    mock_account_service.get_account.return_value = None

    # Generate a random account ID
    random_id = str(uuid.uuid4())

    # Attempt to create a transaction
    response = client.post(
        f"/accounts/{random_id}/transactions",
        json={
            "amount": 100.00,
            "description": "Test Transaction",
            "transaction_type": "credit",
        },
    )

    # Verify response
    assert response.status_code == 404
    data = response.json()
    assert data["error_code"] == "NOT_FOUND"

    # Verify mock was called with correct argument
    mock_account_service.get_account.assert_called_once_with(random_id)
    mock_account_service.credit_account.assert_not_called()


def test_zero_amount_transaction(client, mock_account_service):
    """Test creating transaction with zero amount (should fail validation)"""
    # Set up test account ID
    account_id = str(uuid.uuid4())

    # Configure mock for account existence check
    mock_account_service.get_account.return_value = {
        "account_id": account_id,
        "balance": 1000.00,
    }

    # Make request with zero amount
    response = client.post(
        f"/accounts/{account_id}/transactions",
        json={
            "amount": 0.0,
            "description": "Zero Amount",
            "transaction_type": "credit",
        },
    )

    # Verify response (should be a validation error)
    assert response.status_code == 422  # Validation error

    # No need to check mocks since validation happens before any service calls


def test_negative_amount_transaction(client, mock_account_service):
    """Test creating transaction with negative amount (should fail validation)"""
    # Set up test account ID
    account_id = str(uuid.uuid4())

    # Configure mock for account existence check
    mock_account_service.get_account.return_value = {
        "account_id": account_id,
        "balance": 1000.00,
    }

    # Make request with negative amount
    response = client.post(
        f"/accounts/{account_id}/transactions",
        json={
            "amount": -50.0,
            "description": "Negative Amount",
            "transaction_type": "credit",
        },
    )

    # Verify response (should be a validation error)
    assert response.status_code == 422  # Validation error

    # No need to check mocks since validation happens before any service calls


def test_account_service_down(client, mock_account_service):
    """Test behavior when account service is down"""

    # Configure mock to simulate connection error
    def connection_error(*args, **kwargs):
        # Instead of raising an HTTPException directly, simulate a regular exception
        # that will be caught by the route's exception handler
        raise Exception("Failed to communicate with account service")

    mock_account_service.get_account.side_effect = connection_error

    # Generate a random account ID
    random_id = str(uuid.uuid4())

    # Make request
    response = client.get(f"/accounts/{random_id}/transactions")

    # Verify response
    assert response.status_code == 500
    data = response.json()
    assert data["error_code"] == "INTERNAL_ERROR"
    assert (
        "account service" in data["message"].lower()
        or "server error" in data["message"].lower()
    )
