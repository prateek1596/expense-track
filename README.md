# Spend - Indian Expense Tracker

Spend is a full-stack expense tracking app focused on Indian bank integrations via the Account Aggregator (AA) ecosystem.

## What this scaffold includes

- FastAPI backend with:
  - JWT auth
  - Bank account linking endpoints (Setu AA sandbox ready)
  - Transaction ingestion + auto-categorization
  - Monthly report API
  - Webhook endpoint for near real-time updates
  - WebSocket stream for live dashboard updates
- React + Vite frontend with:
  - Dashboard summary cards
  - Live transaction feed
  - Bank linking form
  - Monthly category report chart/list
- Docker Compose for local development:
  - API
  - Web app
  - PostgreSQL
  - Redis

## Quick start

1. Copy backend environment file (only if `backend/.env` is missing):

```bash
cp backend/.env.example backend/.env
```

On Windows PowerShell:

```powershell
Copy-Item backend/.env.example backend/.env
```

2. Start all services:

```bash
docker compose up --build
```

3. Open apps:
- Frontend: http://localhost:5173
- Backend docs: http://localhost:8000/docs

## Implemented API surface

- Auth:
  - `POST /auth/register`
  - `POST /auth/login`
  - `GET /auth/me`
- Accounts:
  - `GET /accounts`
  - `POST /accounts/link`
- Transactions:
  - `GET /transactions`
  - `POST /transactions`
- Reports:
  - `GET /reports/monthly?month=MM&year=YYYY`
- Realtime:
  - `POST /webhooks/setu`
  - `WS /ws/{user_id}`

## Important note on Indian bank integration

In India, direct per-bank transaction APIs are usually not publicly available for individual developers.
This scaffold uses a Setu Account Aggregator style integration module and webhook architecture.
For production, you need FIU compliance and approved AA onboarding.

## Suggested next steps

1. Plug actual Setu sandbox credentials in `backend/.env`.
2. Implement webhook signature validation from Setu docs.
3. Add Alembic migrations and robust test coverage.
4. Build richer categorization rules or an ML model.
