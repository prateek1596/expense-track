import hashlib
import hmac
import json
from datetime import datetime
from unittest.mock import AsyncMock

import pytest
from fastapi.testclient import TestClient

from app.database import get_db
from app.main import app
from app.models import BankAccount
from app.routers import webhooks


class FakeQuery:
    def __init__(self, account):
        self._account = account

    def filter(self, *args, **kwargs):
        return self

    def first(self):
        return self._account


class FakeDB:
    def __init__(self, account):
        self._account = account
        self.added = []
        self.committed = False

    def query(self, model):
        return FakeQuery(self._account)

    def add(self, item):
        self.added.append(item)

    def commit(self):
        self.committed = True


@pytest.fixture()
def client_with_overrides():
    account = BankAccount(
        id=1,
        user_id=42,
        bank_name="HDFC",
        masked_account="XXXX4321",
        aa_consent_id="consent-1",
        linked_at=datetime.utcnow(),
    )
    db = FakeDB(account)
    previous_overrides = dict(app.dependency_overrides)
    app.dependency_overrides[get_db] = lambda: db
    try:
        yield TestClient(app), db
    finally:
        app.dependency_overrides = previous_overrides


def test_setu_webhook_creates_transactions_and_validates_signature(monkeypatch, client_with_overrides):
    client, db = client_with_overrides
    secret = "webhook-secret"
    monkeypatch.setattr(webhooks.settings, "setu_webhook_secret", secret)
    monkeypatch.setattr(webhooks.settings, "setu_webhook_signature_header", "x-setu-signature")

    budget_alerts = AsyncMock()
    broadcast = AsyncMock()
    monkeypatch.setattr(webhooks, "evaluate_and_notify_budget", budget_alerts)
    monkeypatch.setattr(webhooks.manager, "broadcast_to_user", broadcast)

    body = json.dumps(
        {
            "account_id": 1,
            "transactions": [
                {
                    "amount": 249.5,
                    "tx_type": "debit",
                    "merchant": "Swiggy",
                    "description": "Dinner order",
                    "timestamp": "2026-04-28T10:00:00",
                }
            ],
        },
        separators=(",", ":"),
    ).encode("utf-8")
    signature = hmac.new(secret.encode("utf-8"), body, hashlib.sha256).hexdigest()

    response = client.post(
        "/webhooks/setu",
        content=body,
        headers={"content-type": "application/json", "x-setu-signature": signature},
    )

    assert response.status_code == 200
    assert response.json() == {"status": "ok", "created": 1}
    assert db.committed is True
    assert len(db.added) == 1
    assert db.added[0].user_id == 42
    assert db.added[0].category == "Food"
    budget_alerts.assert_awaited_once()
    broadcast.assert_awaited_once_with(42, {"type": "transaction.batch_created", "count": 1})


def test_setu_webhook_rejects_invalid_signature(monkeypatch, client_with_overrides):
    client, _db = client_with_overrides
    monkeypatch.setattr(webhooks.settings, "setu_webhook_secret", "webhook-secret")
    monkeypatch.setattr(webhooks.settings, "setu_webhook_signature_header", "x-setu-signature")

    body = json.dumps({"account_id": 1, "transactions": []}, separators=(",", ":")).encode("utf-8")

    response = client.post(
        "/webhooks/setu",
        content=body,
        headers={"content-type": "application/json", "x-setu-signature": "bad-signature"},
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid webhook signature"