# transactions/clients/accounts_client.py
"""
Client for communicating with the Accounts Service API.
"""
import os
from typing import Dict, Optional

import httpx
from fastapi import HTTPException, status

from transactions.api.models import ErrorCode, ErrorResponse


class AccountsClient:
    """Client for interacting with the Accounts Service API."""

    def __init__(self):
        """Initialize the accounts client with base URL from environment."""
        self.base_url = os.getenv("ACCOUNTS_SERVICE_URL", "http://localhost:8081")
        self.timeout = float(os.getenv("ACCOUNTS_SERVICE_TIMEOUT", "5.0"))

    async def get_account(self, account_id: str) -> Optional[Dict]:
        """
        Get account details from the accounts service.

        Args:
            account_id: The ID of the account to retrieve

        Returns:
            The account details if found, None if not found

        Raises:
            HTTPException: For service errors
        """
        url = f"{self.base_url}/accounts/{account_id}"

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(url)

                if response.status_code == status.HTTP_200_OK:
                    return response.json()

                if response.status_code == status.HTTP_404_NOT_FOUND:
                    return None

                # Handle other error cases
                error_data = response.json()
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Account service error: {error_data.get('message', 'Unknown error')}",
                )

        except httpx.RequestError as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Account service connection error: {str(e)}",
            )

    async def debit_account(self, account_id: str, amount: float) -> Dict:
        """
        Debit an account in the accounts service.

        Args:
            account_id: The ID of the account to debit
            amount: The amount to debit

        Returns:
            The updated account details

        Raises:
            HTTPException: For service errors or insufficient funds
        """
        url = f"{self.base_url}/accounts/{account_id}/debit"
        payload = {"amount": amount}

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(url, json=payload)

                if response.status_code == status.HTTP_200_OK:
                    return response.json()

                error_data = response.json()

                if response.status_code == status.HTTP_404_NOT_FOUND:
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail=ErrorResponse(
                            error_code=ErrorCode.NOT_FOUND,
                            message=f"Account Not Found: {error_data.get('message', 'Account does not exist')}",
                        ).model_dump(),
                    )

                if response.status_code == status.HTTP_400_BAD_REQUEST:
                    if error_data.get("error_code") == "INSUFFICIENT_FUNDS":
                        raise HTTPException(
                            status_code=status.HTTP_400_BAD_REQUEST,
                            detail=ErrorResponse(
                                error_code=ErrorCode.INSUFFICIENT_FUNDS,
                                message=f"Insufficient Funds: {error_data.get('message', 'Account balance too low')}",
                            ).model_dump(),
                        )
                    else:
                        raise HTTPException(
                            status_code=status.HTTP_400_BAD_REQUEST,
                            detail=ErrorResponse(
                                error_code=ErrorCode.BAD_REQUEST,
                                message=f"Bad Request: {error_data.get('message', 'Invalid request')}",
                            ).model_dump(),
                        )

                # Handle other error cases
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=ErrorResponse(
                        error_code=ErrorCode.INTERNAL_ERROR,
                        message=f"Account Service Error: {error_data.get('message', 'Unknown error')}",
                    ).model_dump(),
                )

        except httpx.RequestError as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=ErrorResponse(
                    error_code=ErrorCode.INTERNAL_ERROR,
                    message=f"Account Service Error: Failed to communicate with account service - {str(e)}",
                ).model_dump(),
            )

    async def credit_account(self, account_id: str, amount: float) -> Dict:
        """
        Credit an account in the accounts service.

        Args:
            account_id: The ID of the account to credit
            amount: The amount to credit

        Returns:
            The updated account details

        Raises:
            HTTPException: For service errors
        """
        url = f"{self.base_url}/accounts/{account_id}/credit"
        payload = {"amount": amount}

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(url, json=payload)

                if response.status_code == status.HTTP_200_OK:
                    return response.json()

                error_data = response.json()

                if response.status_code == status.HTTP_404_NOT_FOUND:
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail=ErrorResponse(
                            error_code=ErrorCode.NOT_FOUND,
                            message=f"Account Not Found: {error_data.get('message', 'Account does not exist')}",
                        ).model_dump(),
                    )

                if response.status_code == status.HTTP_400_BAD_REQUEST:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=ErrorResponse(
                            error_code=ErrorCode.BAD_REQUEST,
                            message=f"Bad Request: {error_data.get('message', 'Invalid request')}",
                        ).model_dump(),
                    )

                # Handle other error cases
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=ErrorResponse(
                        error_code=ErrorCode.INTERNAL_ERROR,
                        message=f"Account Service Error: {error_data.get('message', 'Unknown error')}",
                    ).model_dump(),
                )

        except httpx.RequestError as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=ErrorResponse(
                    error_code=ErrorCode.INTERNAL_ERROR,
                    message=f"Account Service Error: Failed to communicate with account service - {str(e)}",
                ).model_dump(),
            )

    async def check_health(self) -> bool:
        """
        Check if the accounts service is healthy.

        Returns:
            True if healthy, False otherwise
        """
        url = f"{self.base_url}/health"

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(url)
                return response.status_code == status.HTTP_200_OK
        except httpx.RequestError:
            return False


# Create a singleton instance
accounts_client = AccountsClient()
