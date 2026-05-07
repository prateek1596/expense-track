# Spend API Documentation

Complete API reference for the Spend expense tracker backend (FastAPI).

## Base URL

- **Development**: `http://localhost:8000`
- **Production**: Configurable via `API_BASE_URL` environment variable

## Authentication

All endpoints except `/auth/register`, `/auth/login`, and `/health` require JWT bearer token authentication.

**Header**: `Authorization: Bearer <token>`

**Token Format**: JWT token obtained from login/register endpoints

## Response Format

All responses are JSON with the following structure:

- **Success (2xx)**: Returns requested data or success message
- **Error (4xx/5xx)**: Returns error object with `detail` field

```json
{
  "detail": "Error message describing what went wrong"
}
```

---

## Endpoints

### Authentication

#### POST /auth/register

Register a new user account.

**Request Body**:
```json
{
  "email": "user@example.com",
  "password": "securepassword",
  "full_name": "User Name"
}
```

**Response** (201):
```json
{
  "id": 1,
  "email": "user@example.com",
  "full_name": "User Name",
  "created_at": "2026-04-28T10:30:00Z"
}
```

**Errors**:
- `400`: Duplicate email, invalid email format, missing fields
- `400`: Password too short or empty

---

#### POST /auth/login

Authenticate user and obtain JWT token.

**Request Body**:
```json
{
  "email": "user@example.com",
  "password": "securepassword"
}
```

**Response** (200):
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "user": {
    "id": 1,
    "email": "user@example.com",
    "full_name": "User Name"
  }
}
```

**Errors**:
- `401`: Invalid credentials
- `404`: User not found
- `400`: Missing email or password

---

#### GET /auth/me

Get current authenticated user's profile.

**Headers**: `Authorization: Bearer <token>`

**Response** (200):
```json
{
  "id": 1,
  "email": "user@example.com",
  "full_name": "User Name",
  "created_at": "2026-04-28T10:30:00Z"
}
```

**Errors**:
- `401`: Missing or invalid token

---

### Bank Accounts

#### GET /accounts

List all linked bank accounts for the current user.

**Headers**: `Authorization: Bearer <token>`

**Query Parameters**:
- None

**Response** (200):
```json
[
  {
    "id": 1,
    "user_id": 1,
    "bank_name": "HDFC",
    "masked_account": "XXXX4321",
    "aa_consent_id": "consent-abc123",
    "linked_at": "2026-04-28T10:30:00Z"
  },
  {
    "id": 2,
    "user_id": 1,
    "bank_name": "ICICI",
    "masked_account": "XXXX8765",
    "aa_consent_id": "consent-def456",
    "linked_at": "2026-04-29T15:45:00Z"
  }
]
```

**Errors**:
- `401`: Missing or invalid token

---

#### POST /accounts/consent-url

Generate a Setu Account Aggregator consent URL for linking a bank account.

**Headers**: `Authorization: Bearer <token>`

**Request Body**:
```json
{
  "bank_name": "HDFC",
  "phone": "9876543210"
}
```

**Response** (200):
```json
{
  "consent_url": "https://setu.sandbox.onemoney.in/...",
  "consent_id": "consent-abc123"
}
```

**Errors**:
- `401`: Missing or invalid token
- `500`: Setu API error

---

### Transactions

#### GET /transactions

List transactions for the current user with optional filtering.

**Headers**: `Authorization: Bearer <token>`

**Query Parameters**:
- `account_id` (optional): Filter by specific bank account
- `month` (optional): Month (1-12), defaults to current month
- `year` (optional): Year, defaults to current year
- `category` (optional): Filter by category (e.g., "Food & Dining", "Transport")
- `search` (optional): Search in merchant name or description

**Response** (200):
```json
[
  {
    "id": 1,
    "user_id": 1,
    "account_id": 1,
    "amount": 250.50,
    "tx_type": "debit",
    "merchant": "Swiggy",
    "category": "Food & Dining",
    "description": "Dinner order",
    "timestamp": "2026-04-28T19:30:00Z",
    "raw_data": {}
  },
  {
    "id": 2,
    "user_id": 1,
    "account_id": 1,
    "amount": 1500.00,
    "tx_type": "debit",
    "merchant": "Amazon",
    "category": "Shopping",
    "description": "Book purchase",
    "timestamp": "2026-04-29T14:20:00Z",
    "raw_data": {}
  }
]
```

**Errors**:
- `401`: Missing or invalid token

---

#### POST /transactions

Create a manual transaction entry (for testing or manual additions).

**Headers**: `Authorization: Bearer <token>`

**Request Body**:
```json
{
  "account_id": 1,
  "amount": 250.50,
  "tx_type": "debit",
  "merchant": "Swiggy",
  "description": "Dinner order"
}
```

**Response** (201):
```json
{
  "id": 3,
  "user_id": 1,
  "account_id": 1,
  "amount": 250.50,
  "tx_type": "debit",
  "merchant": "Swiggy",
  "category": "Food & Dining",
  "description": "Dinner order",
  "timestamp": "2026-04-28T19:30:00Z",
  "raw_data": {}
}
```

**Errors**:
- `401`: Missing or invalid token
- `400`: Missing required fields or invalid data

---

### Budgets

#### GET /budgets

List all budget limits set by the current user for the current month.

**Headers**: `Authorization: Bearer <token>`

**Query Parameters**:
- `month` (optional): Month (1-12), defaults to current
- `year` (optional): Year, defaults to current

**Response** (200):
```json
[
  {
    "id": 1,
    "user_id": 1,
    "category": "Food & Dining",
    "limit": 5000.00,
    "month": 4,
    "year": 2026,
    "created_at": "2026-04-28T10:30:00Z"
  },
  {
    "id": 2,
    "user_id": 1,
    "category": "Transport",
    "limit": 3000.00,
    "month": 4,
    "year": 2026,
    "created_at": "2026-04-28T11:45:00Z"
  }
]
```

**Errors**:
- `401`: Missing or invalid token

---

#### POST /budgets

Create or update a monthly budget limit for a category.

**Headers**: `Authorization: Bearer <token>`

**Request Body**:
```json
{
  "category": "Food & Dining",
  "limit": 5000.00,
  "month": 4,
  "year": 2026
}
```

**Response** (201):
```json
{
  "id": 1,
  "user_id": 1,
  "category": "Food & Dining",
  "limit": 5000.00,
  "month": 4,
  "year": 2026,
  "created_at": "2026-04-28T10:30:00Z"
}
```

**Errors**:
- `401`: Missing or invalid token
- `400`: Missing required fields or invalid category

---

### Reports

#### GET /reports/monthly

Get monthly spending summary with category breakdown.

**Headers**: `Authorization: Bearer <token>`

**Query Parameters**:
- `month` (optional): Month (1-12), defaults to current
- `year` (optional): Year, defaults to current

**Response** (200):
```json
{
  "total": 8500.50,
  "month": 4,
  "year": 2026,
  "by_category": {
    "Food & Dining": 2500.50,
    "Transport": 1200.00,
    "Shopping": 3500.00,
    "Entertainment": 800.00,
    "Other": 500.00
  }
}
```

**Errors**:
- `401`: Missing or invalid token

---

#### GET /reports/recurring

Get recurring spending patterns based on historical data.

**Headers**: `Authorization: Bearer <token>`

**Query Parameters**:
- None

**Response** (200):
```json
[
  {
    "merchant": "Swiggy",
    "category": "Food & Dining",
    "average_amount": 250.00,
    "frequency": "weekly",
    "last_transaction": "2026-04-28T19:30:00Z",
    "count": 12
  },
  {
    "merchant": "Netflix",
    "category": "Entertainment",
    "average_amount": 200.00,
    "frequency": "monthly",
    "last_transaction": "2026-04-01T10:00:00Z",
    "count": 5
  }
]
```

**Errors**:
- `401`: Missing or invalid token

---

### Webhooks

#### POST /webhooks/setu

Receive transaction updates from Setu Account Aggregator.

**Headers**: 
- `X-Setu-Signature`: HMAC-SHA256 signature of request body

**Request Body** (from Setu):
```json
{
  "timestamp": "2026-04-28T19:30:00Z",
  "data": [
    {
      "id": "tx-1",
      "amount": 250.50,
      "type": "debit",
      "merchant": "Swiggy",
      "description": "Dinner order",
      "account_id": "acc-123"
    }
  ]
}
```

**Response** (200):
```json
{
  "status": "ok",
  "created": 1
}
```

**Errors**:
- `400`: Invalid signature
- `400`: Malformed payload
- `500`: Processing error

---

### WebSocket

#### GET /ws/{user_id}

WebSocket connection for real-time transaction updates and alerts.

**URL**: `ws://localhost:8000/ws/0` (0 for demo, replace with actual user_id)

**Incoming Messages**: Server broadcasts new transactions and budget alerts

```json
{
  "type": "transaction.batch_created",
  "count": 1
}
```

```json
{
  "type": "budget_alert",
  "data": {
    "budget_id": 1,
    "category": "Food & Dining",
    "spent": 5200.00,
    "limit": 5000.00,
    "percentage": 104
  }
}
```

---

### Health Check

#### GET /health

Check API health and readiness.

**Response** (200):
```json
{
  "status": "ok"
}
```

---

## Transaction Categories

The following categories are automatically assigned during transaction ingestion:

- Food & Dining
- Transport
- Shopping
- Utilities
- Health & Fitness
- Entertainment
- Education
- Transfer & Payment
- Insurance
- Rent & Housing
- Other

---

## Rate Limiting

Currently no rate limiting is implemented. In production, recommend implementing:
- Per-user rate limits (e.g., 100 requests/minute)
- Per-endpoint limits based on computational cost
- Webhook delivery retry logic with exponential backoff

---

## Error Codes

### Authentication Errors (4xx)
- `400 Bad Request`: Invalid email format, missing fields
- `401 Unauthorized`: Invalid credentials, missing token
- `404 Not Found`: User not found

### Validation Errors (4xx)
- `400 Bad Request`: Invalid amount, unsupported category, missing required fields
- `422 Unprocessable Entity`: Data validation failed

### Server Errors (5xx)
- `500 Internal Server Error`: Unexpected server error
- `503 Service Unavailable`: Database connection error

---

## Example Workflows

### Complete Login & View Transactions Flow

1. **Register User**:
   ```bash
   curl -X POST http://localhost:8000/auth/register \
     -H "Content-Type: application/json" \
     -d '{"email":"user@example.com","password":"pass123","full_name":"John Doe"}'
   ```

2. **Login**:
   ```bash
   curl -X POST http://localhost:8000/auth/login \
     -H "Content-Type: application/json" \
     -d '{"email":"user@example.com","password":"pass123"}'
   ```

3. **Get Current User** (use token from login):
   ```bash
   curl -X GET http://localhost:8000/auth/me \
     -H "Authorization: Bearer <token>"
   ```

4. **List Accounts**:
   ```bash
   curl -X GET http://localhost:8000/accounts \
     -H "Authorization: Bearer <token>"
   ```

5. **List Transactions**:
   ```bash
   curl -X GET "http://localhost:8000/transactions?month=4&year=2026" \
     -H "Authorization: Bearer <token>"
   ```

6. **Create Budget**:
   ```bash
   curl -X POST http://localhost:8000/budgets \
     -H "Authorization: Bearer <token>" \
     -H "Content-Type: application/json" \
     -d '{"category":"Food & Dining","limit":5000,"month":4,"year":2026}'
   ```

7. **Get Monthly Report**:
   ```bash
   curl -X GET "http://localhost:8000/reports/monthly?month=4&year=2026" \
     -H "Authorization: Bearer <token>"
   ```

---

## Environment Variables

- `DATABASE_URL`: PostgreSQL connection string
- `SETU_AA_CLIENT_ID`: Setu Account Aggregator client ID
- `SETU_AA_SECRET`: Setu AA secret key
- `SETU_AA_WEBHOOK_SECRET`: Webhook signature validation secret
- `JWT_SECRET`: JWT signing secret
- `JWT_ALGORITHM`: JWT algorithm (default: HS256)
- `JWT_EXPIRY_HOURS`: Token expiry in hours (default: 24)

---

## Version History

- **v1.0** (April 2026): Initial release with core features
  - User authentication
  - Bank account linking via Setu AA
  - Transaction ingestion and categorization
  - Monthly budget management
  - Spending reports
  - Real-time WebSocket updates

---

**Last Updated**: May 7, 2026
