# Transactions Service

A RESTful API microservice for recording and retrieving financial transactions, designed to integrate with the Accounts service in a microservices architecture.

## Features

- Record credit and debit transactions for accounts
- Communicate with Accounts service to update balances
- Retrieve transaction history for accounts
- Validate transaction amounts and check for sufficient funds
- Health check endpoints with dependency monitoring
- Robust error handling with standardized responses

## Architecture

This service follows microservice architecture principles:
- **Transaction Storage**: Maintains a record of all transactions
- **Account Integration**: Communicates with the Accounts service for balance operations
- **Stateless Design**: No local balance management, ensuring data consistency

## Project Structure

```
.
├── transactions/           # Main package
│   ├── __init__.py
│   ├── api/                # API modules
│   │   ├── __init__.py
│   │   ├── models.py       # Pydantic models
│   │   └── routes.py       # Route definitions
│   ├── clients/            # Service clients
│   │   └── accounts_client.py # Accounts service client
│   ├── services/           # Business logic
│   │   ├── __init__.py
│   │   └── transaction.py  # Transaction operations
│   └── main.py             # App entry point
├── tests/                  # Test directory
│   ├── __init__.py
│   ├── conftest.py         # Test fixtures
│   ├── test_api.py         # API tests
│   ├── test_accounts_client.py # Client tests
│   └── test_service.py     # Service tests
├── Dockerfile              # Docker configuration
├── docker-compose.yaml     # Docker Compose setup
├── Makefile                # Build automation
├── pyproject.toml          # Poetry config
└── README.md               # This file
```

## Development Setup

### Prerequisites

- Python 3.11+
- Poetry (Python package manager)
- Docker & Docker Compose (for containerization)
- Access to the Accounts service (real or mocked)

### Local Development

1. Install dependencies:

```bash
make setup
```

2. Run the service locally:

```bash
make run
```

The service will start at http://localhost:8082 and will attempt to connect to the Accounts service at the URL specified by the `ACCOUNTS_SERVICE_URL` environment variable (default: http://localhost:8081).

3. Run tests:

```bash
make test
```

4. Lint code:

```bash
make lint
```

### Docker Development

1. Build the Docker image:

```bash
make docker-build
```

2. Run with Docker Compose (includes Accounts service):

```bash
make docker-compose-up
```

This will start both the Transactions service and the Accounts service, with proper connection between them.

3. Stop Docker Compose services:

```bash
make docker-compose-down
```

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `ACCOUNTS_SERVICE_URL` | URL of the Accounts service | `http://localhost:8081` |
| `ACCOUNTS_SERVICE_TIMEOUT` | Timeout for Accounts service requests (seconds) | `5.0` |

## API Endpoints

### Health Check
- `GET /health` - Service health check (includes Accounts service status)
- `HEAD /health` - Health check without response body

### Transactions
- `GET /accounts/{account_id}/transactions` - List all transactions for an account
- `POST /accounts/{account_id}/transactions` - Record a new transaction for an account

## API Usage

### Creating a Transaction

```python
import requests

# Example account ID
account_id = "123e4567-e89b-12d3-a456-426614174000"

# Credit transaction
credit_response = requests.post(
    f"http://localhost:8082/accounts/{account_id}/transactions",
    json={
        "amount": 500.00,
        "description": "Salary Payment",
        "transaction_type": "credit"
    }
)

# Debit transaction
debit_response = requests.post(
    f"http://localhost:8082/accounts/{account_id}/transactions",
    json={
        "amount": 200.00,
        "description": "Grocery Shopping",
        "transaction_type": "debit"
    }
)
```

### Retrieving Transactions

```python
import requests

# Get all transactions for an account
response = requests.get(f"http://localhost:8082/accounts/{account_id}/transactions")
transactions = response.json()
```

## Error Handling

The service provides standardized error responses:

```json
{
  "error_code": "ERROR_TYPE",
  "message": "Human-readable error message"
}
```

Error codes:
- `NOT_FOUND` - Account not found
- `BAD_REQUEST` - Invalid request parameters
- `INSUFFICIENT_FUNDS` - Insufficient balance for debit
- `INTERNAL_ERROR` - Server or integration error

## Integration Testing

To run the service with a mock Accounts service:

```bash
# In one terminal, run the mock Accounts service
cd path/to/accounts-service
make run

# In another terminal, run the Transactions service
cd path/to/transactions-service
make run
```

For full integration testing, the docker-compose setup includes both services.

## Docker Hub Deployment

This repository is set up to build and publish Docker images to Docker Hub.

1. Set your Docker Hub username in the Makefile:

```makefile
IMAGE_NAME := your-dockerhub-username/transactions
```

2. Build and push the image:

```bash
make publish
```

## Using with Kong API Gateway

This service is designed to be used with Kong API Gateway for demonstrations. When combined with the Accounts service, it provides a complete banking API system that can demonstrate:

- Service communication patterns
- API gateway routing
- Authentication and authorization
- Rate limiting
- Request transformation

## License

MIT
