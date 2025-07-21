# transactions/main.py
"""
Entry point for the Transactions API.
A microservice for recording and retrieving financial transactions.
"""
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI, status
from fastapi.responses import JSONResponse

from transactions.api.models import HealthResponse
from transactions.api.routes import router
from transactions.services.transaction import transaction_service


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for handling startup and shutdown events"""
    # No initialization needed since we're using the accounts service
    yield


# Create FastAPI app
app = FastAPI(
    title="Transactions API",
    description="This API manages the recording and retrieval of account transactions.",
    version="1.0.0",
    lifespan=lifespan,
)

# Include API routes
app.include_router(router)


# Health check endpoints
@app.get(
    "/health",
    tags=["health"],
    response_model=HealthResponse,
    summary="Check service health",
)
async def health_check():
    """Returns the API's health status"""
    # Check the health of the account service
    account_service_health = await transaction_service.check_account_service_health()

    if account_service_health:
        return HealthResponse(
            status="UP", account_service="UP", message="All services operational"
        )
    else:
        response = HealthResponse(
            status="UP", account_service="DOWN", message="Account service not available"
        )
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content=response.model_dump(),
        )


@app.head("/health", tags=["health"], summary="Check service health (HEAD)")
async def health_check_head():
    """Returns the API's health status without body"""
    # Check the health of the account service
    account_service_health = await transaction_service.check_account_service_health()

    if not account_service_health:
        return JSONResponse(status_code=status.HTTP_503_SERVICE_UNAVAILABLE)
    return None


def main():
    """Run the application with uvicorn"""
    uvicorn.run(app, host="0.0.0.0", port=8082)


if __name__ == "__main__":
    main()
