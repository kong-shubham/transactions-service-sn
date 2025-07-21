"""
Pydantic models for the Transactions API.
"""

from datetime import datetime
from enum import Enum
from typing import Literal

from pydantic import BaseModel, Field


class ErrorCode(str, Enum):
    """Error codes for API responses"""

    INTERNAL_ERROR = "INTERNAL_ERROR"
    NOT_FOUND = "NOT_FOUND"
    BAD_REQUEST = "BAD_REQUEST"
    INSUFFICIENT_FUNDS = "INSUFFICIENT_FUNDS"


class Transaction(BaseModel):
    """Transaction model representing a financial transaction"""

    transaction_id: str
    date: datetime
    amount: float
    description: str
    transaction_type: Literal["debit", "credit"]


class TransactionRequest(BaseModel):
    """Request model for creating a new transaction"""

    amount: float = Field(gt=0)
    description: str
    transaction_type: Literal["debit", "credit"]


class HealthResponse(BaseModel):
    """Response model for health check endpoint"""

    status: str
    account_service: str
    message: str


class ErrorResponse(BaseModel):
    """Error response model"""

    error_code: ErrorCode
    message: str
