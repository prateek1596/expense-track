from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.routers import accounts, auth, budgets, reports, transactions, webhooks, ws, scheduled_exports
from app.config import settings
from app.services import scheduler as scheduler_service

app = FastAPI(
    title="Spend API",
    version="0.1.0",
    description=(
        "Spend is a demo expense-tracking API focused on Indian bank integrations via "
        "an Account Aggregator (AA) style flow. Includes auth, accounts, transactions, "
        "budgets, reports, webhooks and WebSocket-based realtime updates."
    ),
    contact={"name": "Spend Dev Team", "email": "dev@example.com"},
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_origin, "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health():
    return {"status": "ok"}


app.include_router(auth.router)
app.include_router(accounts.router)
app.include_router(transactions.router)
app.include_router(reports.router)
app.include_router(budgets.router)
app.include_router(webhooks.router)
app.include_router(ws.router)
app.include_router(scheduled_exports.router)


@app.on_event("startup")
def _startup():
    if settings.enable_scheduler:
        try:
            scheduler_service.init_scheduler(app)
        except Exception:
            # make startup resilient in dev/test environments
            pass
