# transactions/api/routes.py
"""
API routes for the Transactions Service.
"""
from typing import List
from uuid import UUID

from fastapi import APIRouter, HTTPException, Path, status
from fastapi.responses import JSONResponse

from transactions.api.models import (
    ErrorCode,
    ErrorResponse,
    Transaction,
    TransactionRequest,
)
from transactions.services.transaction import transaction_service

# Create router for transactions
router = APIRouter()


@router.get(
    "/accounts/{account_id}/transactions",
    tags=["transactions"],
    response_model=List[Transaction],
    responses={
        404: {"model": ErrorResponse, "description": "Account not found"},
        500: {"model": ErrorResponse, "description": "Internal server error"},
    },
)
async def get_transactions_for_account(
    account_id: UUID = Path(..., description="The UUID of the account")
):
    """Returns a list of all transactions for an account."""
    try:
        account_id_str = str(account_id)

        # Check if account exists
        if not await transaction_service.account_exists(account_id_str):
            error_response = ErrorResponse(
                error_code=ErrorCode.NOT_FOUND,
                message=f"Account {account_id} Not Found",
            )
            return JSONResponse(
                status_code=status.HTTP_404_NOT_FOUND,
                content=error_response.model_dump(),
            )

        # Get transactions for the account
        return await transaction_service.get_transactions(account_id_str)

    except HTTPException as e:
        raise e
    except Exception as e:
        error_response = ErrorResponse(
            error_code=ErrorCode.INTERNAL_ERROR,
            message=f"Internal Server Error: {str(e)}",
        )
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=error_response.model_dump(),
        )


@router.post(
    "/accounts/{account_id}/transactions",
    tags=["transactions"],
    response_model=Transaction,
    status_code=status.HTTP_201_CREATED,
    responses={
        400: {
            "model": ErrorResponse,
            "description": "Bad request or insufficient funds",
        },
        404: {"model": ErrorResponse, "description": "Account not found"},
        500: {"model": ErrorResponse, "description": "Internal server error"},
    },
)
async def create_transaction_for_account(
    transaction_request: TransactionRequest,
    account_id: UUID = Path(..., description="The UUID of the account"),
):
    """Creates a new transaction for an account."""
    try:
        account_id_str = str(account_id)

        # Check if account exists
        if not await transaction_service.account_exists(account_id_str):
            error_response = ErrorResponse(
                error_code=ErrorCode.NOT_FOUND,
                message="Account Not Found: Account does not exist",
            )
            return JSONResponse(
                status_code=status.HTTP_404_NOT_FOUND,
                content=error_response.model_dump(),
            )

        # Check amount decimal places
        if round(transaction_request.amount, 2) != transaction_request.amount:
            error_response = ErrorResponse(
                error_code=ErrorCode.BAD_REQUEST,
                message="Bad Transaction: Amount must not have more than 2 decimal places",
            )
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content=error_response.model_dump(),
            )

        # Create transaction
        transaction = await transaction_service.create_transaction(
            account_id=account_id_str,
            amount=transaction_request.amount,
            description=transaction_request.description,
            transaction_type=transaction_request.transaction_type,
        )

        return transaction

    except HTTPException as e:
        # Forward the HTTP exception as is
        if isinstance(e.detail, dict) and "error_code" in e.detail:
            return JSONResponse(
                status_code=e.status_code,
                content=e.detail,
            )
        raise e
    except Exception as e:
        error_response = ErrorResponse(
            error_code=ErrorCode.INTERNAL_ERROR,
            message=f"Internal Server Error: {str(e)}",
        )
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=error_response.model_dump(),
        )
