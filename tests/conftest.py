# tests/conftest.py
"""
Test fixtures for the Transactions service tests.
"""
from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient

from transactions.main import app
from transactions.services.transaction import TransactionService


@pytest.fixture
def client():
    """Test client fixture for API tests"""
    return TestClient(app)


@pytest.fixture
def mock_accounts_client():
    """Mock the accounts client for testing"""
    with patch("transactions.services.transaction.accounts_client") as mock_client:
        # Mock the account_exists method
        mock_client.get_account = AsyncMock()
        mock_client.get_account.return_value = {
            "account_id": "test-account",
            "balance": 1000.0,
        }

        # Mock the debit_account method
        mock_client.debit_account = AsyncMock()
        mock_client.debit_account.return_value = {
            "account_id": "test-account",
            "balance": 800.0,
        }

        # Mock the credit_account method
        mock_client.credit_account = AsyncMock()
        mock_client.credit_account.return_value = {
            "account_id": "test-account",
            "balance": 1200.0,
        }

        # Mock the check_health method
        mock_client.check_health = AsyncMock()
        mock_client.check_health.return_value = True

        yield mock_client


@pytest.fixture
def mock_transaction_service(mock_accounts_client):
    """Fixture that provides a mocked transaction service"""
    service = TransactionService()
    return service


@pytest.fixture
def mock_account_id():
    """Fixture that returns a mock account ID"""
    return "88fd34c4-0450-43d3-b93f-25842c0e3a6c"


@pytest.fixture
def seeded_account(mock_account_id, mock_accounts_client):
    """Fixture that provides a seeded account ID"""
    # Configure mock to recognize this account
    mock_accounts_client.get_account.return_value = {
        "account_id": mock_account_id,
        "balance": 1000.0,
    }
    return mock_account_id
