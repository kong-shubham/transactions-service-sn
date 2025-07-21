"""
Tests for the Accounts Service Client.
"""

from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest
from fastapi import HTTPException

from transactions.clients.accounts_client import AccountsClient

# from transactions.api.models import ErrorCode


@pytest.fixture
def mock_httpx_client():
    """Mock httpx client for testing"""
    with patch("httpx.AsyncClient") as mock_client:
        client_instance = AsyncMock()
        mock_client.return_value.__aenter__.return_value = client_instance
        yield client_instance


@pytest.fixture
def accounts_client_instance():
    """Returns a fresh AccountsClient instance"""
    with patch.object(AccountsClient, "__init__", return_value=None) as _:
        client = AccountsClient()
        client.base_url = "http://test-accounts-service:8081"
        client.timeout = 5.0
        return client


@pytest.mark.asyncio
async def test_get_account_success(accounts_client_instance, mock_httpx_client):
    """Test successfully getting an account"""
    # Setup mock response
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "account_id": "test-account-123",
        "type": "checking",
        "balance": 1000.00,
    }
    mock_httpx_client.get.return_value = mock_response

    # Call the function
    account = await accounts_client_instance.get_account("test-account-123")

    # Verify the result
    assert account["account_id"] == "test-account-123"
    assert account["balance"] == 1000.00

    # Verify mock was called correctly
    mock_httpx_client.get.assert_called_once_with(
        "http://test-accounts-service:8081/accounts/test-account-123"
    )


@pytest.mark.asyncio
async def test_get_account_not_found(accounts_client_instance, mock_httpx_client):
    """Test getting a non-existent account"""
    # Setup mock response
    mock_response = MagicMock()
    mock_response.status_code = 404
    mock_response.json.return_value = {
        "error_code": "NOT_FOUND",
        "message": "Failed to retrieve account: ID not found",
    }
    mock_httpx_client.get.return_value = mock_response

    # Call the function
    account = await accounts_client_instance.get_account("nonexistent-account")

    # Verify the result
    assert account is None

    # Verify mock was called correctly
    mock_httpx_client.get.assert_called_once_with(
        "http://test-accounts-service:8081/accounts/nonexistent-account"
    )


@pytest.mark.asyncio
async def test_get_account_server_error(accounts_client_instance, mock_httpx_client):
    """Test handling server error when getting account"""
    # Setup mock response
    mock_response = MagicMock()
    mock_response.status_code = 500
    mock_response.json.return_value = {
        "error_code": "INTERNAL_ERROR",
        "message": "Internal server error occurred",
    }
    mock_httpx_client.get.return_value = mock_response

    # Call the function and check exception
    with pytest.raises(HTTPException) as excinfo:
        await accounts_client_instance.get_account("test-account-123")

    # Verify the exception
    assert excinfo.value.status_code == 500
    assert "Account service error" in str(excinfo.value.detail)


@pytest.mark.asyncio
async def test_get_account_connection_error(
    accounts_client_instance, mock_httpx_client
):
    """Test handling connection error when getting account"""
    # Setup mock to raise connection error
    mock_httpx_client.get.side_effect = httpx.RequestError("Connection error")

    # Call the function and check exception
    with pytest.raises(HTTPException) as excinfo:
        await accounts_client_instance.get_account("test-account-123")

    # Verify the exception
    assert excinfo.value.status_code == 500
    assert "Account service connection error" in str(excinfo.value.detail)


@pytest.mark.asyncio
async def test_debit_account_success(accounts_client_instance, mock_httpx_client):
    """Test successfully debiting an account"""
    # Setup mock response
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "account_id": "test-account-123",
        "type": "checking",
        "balance": 900.00,  # After debiting 100
    }
    mock_httpx_client.post.return_value = mock_response

    # Call the function
    result = await accounts_client_instance.debit_account("test-account-123", 100.00)

    # Verify the result
    assert result["account_id"] == "test-account-123"
    assert result["balance"] == 900.00

    # Verify mock was called correctly
    mock_httpx_client.post.assert_called_once_with(
        "http://test-accounts-service:8081/accounts/test-account-123/debit",
        json={"amount": 100.00},
    )


@pytest.mark.asyncio
async def test_debit_account_not_found(accounts_client_instance, mock_httpx_client):
    """Test debiting a non-existent account"""
    # Setup mock response
    mock_response = MagicMock()
    mock_response.status_code = 404
    mock_response.json.return_value = {
        "error_code": "NOT_FOUND",
        "message": "Failed to debit account: Account does not exist",
    }
    mock_httpx_client.post.return_value = mock_response

    # Call the function and check exception
    with pytest.raises(HTTPException) as excinfo:
        await accounts_client_instance.debit_account("nonexistent-account", 100.00)

    # Verify the exception
    assert excinfo.value.status_code == 404
    assert "NOT_FOUND" in str(excinfo.value.detail)


@pytest.mark.asyncio
async def test_debit_account_insufficient_funds(
    accounts_client_instance, mock_httpx_client
):
    """Test debiting with insufficient funds"""
    # Setup mock response
    mock_response = MagicMock()
    mock_response.status_code = 400
    mock_response.json.return_value = {
        "error_code": "INSUFFICIENT_FUNDS",
        "message": "Failed to debit account: Insufficient funds - balance is 100.00, attempted to debit 200.00",
    }
    mock_httpx_client.post.return_value = mock_response

    # Call the function and check exception
    with pytest.raises(HTTPException) as excinfo:
        await accounts_client_instance.debit_account("test-account-123", 200.00)

    # Verify the exception
    assert excinfo.value.status_code == 400
    assert "INSUFFICIENT_FUNDS" in str(excinfo.value.detail)


@pytest.mark.asyncio
async def test_debit_account_bad_request(accounts_client_instance, mock_httpx_client):
    """Test debiting with invalid parameters"""
    # Setup mock response
    mock_response = MagicMock()
    mock_response.status_code = 400
    mock_response.json.return_value = {
        "error_code": "INVALID_INPUT",
        "message": "Failed to debit account: Amount must be positive",
    }
    mock_httpx_client.post.return_value = mock_response

    # Call the function and check exception
    with pytest.raises(HTTPException) as excinfo:
        await accounts_client_instance.debit_account("test-account-123", 0)

    # Verify the exception
    assert excinfo.value.status_code == 400
    assert "BAD_REQUEST" in str(excinfo.value.detail)


@pytest.mark.asyncio
async def test_debit_account_server_error(accounts_client_instance, mock_httpx_client):
    """Test handling server error when debiting account"""
    # Setup mock response
    mock_response = MagicMock()
    mock_response.status_code = 500
    mock_response.json.return_value = {
        "error_code": "INTERNAL_ERROR",
        "message": "Internal server error occurred",
    }
    mock_httpx_client.post.return_value = mock_response

    # Call the function and check exception
    with pytest.raises(HTTPException) as excinfo:
        await accounts_client_instance.debit_account("test-account-123", 100.00)

    # Verify the exception
    assert excinfo.value.status_code == 500
    assert "INTERNAL_ERROR" in str(excinfo.value.detail)


@pytest.mark.asyncio
async def test_debit_account_connection_error(
    accounts_client_instance, mock_httpx_client
):
    """Test handling connection error when debiting account"""
    # Setup mock to raise connection error
    mock_httpx_client.post.side_effect = httpx.RequestError("Connection error")

    # Call the function and check exception
    with pytest.raises(HTTPException) as excinfo:
        await accounts_client_instance.debit_account("test-account-123", 100.00)

    # Verify the exception
    assert excinfo.value.status_code == 500
    assert "Account Service Error" in str(excinfo.value.detail)


@pytest.mark.asyncio
async def test_credit_account_success(accounts_client_instance, mock_httpx_client):
    """Test successfully crediting an account"""
    # Setup mock response
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "account_id": "test-account-123",
        "type": "checking",
        "balance": 1100.00,  # After crediting 100
    }
    mock_httpx_client.post.return_value = mock_response

    # Call the function
    result = await accounts_client_instance.credit_account("test-account-123", 100.00)

    # Verify the result
    assert result["account_id"] == "test-account-123"
    assert result["balance"] == 1100.00

    # Verify mock was called correctly
    mock_httpx_client.post.assert_called_once_with(
        "http://test-accounts-service:8081/accounts/test-account-123/credit",
        json={"amount": 100.00},
    )


@pytest.mark.asyncio
async def test_credit_account_not_found(accounts_client_instance, mock_httpx_client):
    """Test crediting a non-existent account"""
    # Setup mock response
    mock_response = MagicMock()
    mock_response.status_code = 404
    mock_response.json.return_value = {
        "error_code": "NOT_FOUND",
        "message": "Failed to credit account: Account does not exist",
    }
    mock_httpx_client.post.return_value = mock_response

    # Call the function and check exception
    with pytest.raises(HTTPException) as excinfo:
        await accounts_client_instance.credit_account("nonexistent-account", 100.00)

    # Verify the exception
    assert excinfo.value.status_code == 404
    assert "NOT_FOUND" in str(excinfo.value.detail)


@pytest.mark.asyncio
async def test_credit_account_bad_request(accounts_client_instance, mock_httpx_client):
    """Test crediting with invalid parameters"""
    # Setup mock response
    mock_response = MagicMock()
    mock_response.status_code = 400
    mock_response.json.return_value = {
        "error_code": "INVALID_INPUT",
        "message": "Failed to credit account: Amount must be positive",
    }
    mock_httpx_client.post.return_value = mock_response

    # Call the function and check exception
    with pytest.raises(HTTPException) as excinfo:
        await accounts_client_instance.credit_account("test-account-123", -50.00)

    # Verify the exception
    assert excinfo.value.status_code == 400
    assert "BAD_REQUEST" in str(excinfo.value.detail)


@pytest.mark.asyncio
async def test_credit_account_server_error(accounts_client_instance, mock_httpx_client):
    """Test handling server error when crediting account"""
    # Setup mock response
    mock_response = MagicMock()
    mock_response.status_code = 500
    mock_response.json.return_value = {
        "error_code": "INTERNAL_ERROR",
        "message": "Internal server error occurred",
    }
    mock_httpx_client.post.return_value = mock_response

    # Call the function and check exception
    with pytest.raises(HTTPException) as excinfo:
        await accounts_client_instance.credit_account("test-account-123", 100.00)

    # Verify the exception
    assert excinfo.value.status_code == 500
    assert "INTERNAL_ERROR" in str(excinfo.value.detail)


@pytest.mark.asyncio
async def test_credit_account_connection_error(
    accounts_client_instance, mock_httpx_client
):
    """Test handling connection error when crediting account"""
    # Setup mock to raise connection error
    mock_httpx_client.post.side_effect = httpx.RequestError("Connection error")

    # Call the function and check exception
    with pytest.raises(HTTPException) as excinfo:
        await accounts_client_instance.credit_account("test-account-123", 100.00)

    # Verify the exception
    assert excinfo.value.status_code == 500
    assert "Account Service Error" in str(excinfo.value.detail)


@pytest.mark.asyncio
async def test_check_health_success(accounts_client_instance, mock_httpx_client):
    """Test successfully checking health"""
    # Setup mock response
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_httpx_client.get.return_value = mock_response

    # Call the function
    result = await accounts_client_instance.check_health()

    # Verify the result
    assert result is True

    # Verify mock was called correctly
    mock_httpx_client.get.assert_called_once_with(
        "http://test-accounts-service:8081/health"
    )


@pytest.mark.asyncio
async def test_check_health_service_down(accounts_client_instance, mock_httpx_client):
    """Test health check when service is down"""
    # Setup mock response
    mock_response = MagicMock()
    mock_response.status_code = 503
    mock_httpx_client.get.return_value = mock_response

    # Call the function
    result = await accounts_client_instance.check_health()

    # Verify the result
    assert result is False


@pytest.mark.asyncio
async def test_check_health_connection_error(
    accounts_client_instance, mock_httpx_client
):
    """Test health check with connection error"""
    # Setup mock to raise connection error
    mock_httpx_client.get.side_effect = httpx.RequestError("Connection error")

    # Call the function
    result = await accounts_client_instance.check_health()

    # Verify the result
    assert result is False


@pytest.mark.asyncio
async def test_client_initialization():
    """Test client initialization with environment variables"""
    # Save original os.getenv
    original_getenv = __import__("os").getenv

    try:
        # Mock os.getenv to return custom values
        with patch("os.getenv") as mock_getenv:
            mock_getenv.side_effect = lambda key, default=None: {
                "ACCOUNTS_SERVICE_URL": "http://custom-url:8888",
                "ACCOUNTS_SERVICE_TIMEOUT": "10.0",
            }.get(key, default)

            # Create a new client instance
            client = AccountsClient()

            # Verify the client was initialized with the custom values
            assert client.base_url == "http://custom-url:8888"
            assert client.timeout == 10.0
    finally:
        # Restore original os.getenv
        __import__("os").getenv = original_getenv
