import json
from datetime import datetime
from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient

from app.database import get_db
from app.main import app
from app.models import BankAccount, User


class FakeDB:
    def __init__(self):
        self.users = {}
        self.accounts = {}
        self.transactions = []
        self.budgets = []
        self.last_id = 0

    def add(self, item):
        if isinstance(item, User):
            self.last_id += 1
            item.id = self.last_id
            self.users[item.email] = item
        elif isinstance(item, BankAccount):
            self.last_id += 1
            item.id = self.last_id
            self.accounts[item.id] = item
        else:
            self.last_id += 1
            item.id = self.last_id
            self.transactions.append(item)

    def commit(self):
        pass

    def query(self, model):
        return FakeQuery(model, self)


class FakeQuery:
    def __init__(self, model, db):
        self.model = model
        self.db = db
        self.filters = []

    def filter(self, condition):
        self.filters.append(condition)
        return self

    def first(self):
        if self.model == User:
            for user in self.db.users.values():
                return user
        elif self.model == BankAccount:
            for account in self.db.accounts.values():
                return account
        return None

    def all(self):
        if self.model == User:
            return list(self.db.users.values())
        elif self.model == BankAccount:
            return list(self.db.accounts.values())
        return []


@pytest.fixture
def client_with_db():
    db = FakeDB()
    previous_overrides = dict(app.dependency_overrides)
    app.dependency_overrides[get_db] = lambda: db
    try:
        yield TestClient(app), db
    finally:
        app.dependency_overrides = previous_overrides


def test_register_creates_user(client_with_db):
    client, db = client_with_db

    response = client.post(
        "/auth/register",
        json={"email": "alice@example.com", "full_name": "Alice", "password": "pass123"},
    )

    assert response.status_code == 200
    result = response.json()
    assert result["email"] == "alice@example.com"
    assert result["full_name"] == "Alice"
    assert "alice@example.com" in db.users


def test_login_returns_token(client_with_db, monkeypatch):
    client, db = client_with_db

    # Register user first
    client.post(
        "/auth/register",
        json={"email": "bob@example.com", "full_name": "Bob", "password": "pass123"},
    )

    # Mock password verification
    monkeypatch.setattr("app.routers.auth.pwd_context", type("", (), {"verify": lambda s, h, p: True})())

    response = client.post("/auth/login", json={"email": "bob@example.com", "password": "pass123"})

    assert response.status_code == 200
    result = response.json()
    assert "access_token" in result
    assert result["token_type"] == "bearer"


def test_me_returns_authenticated_user(client_with_db, monkeypatch):
    client, db = client_with_db

    # Register and login
    client.post(
        "/auth/register",
        json={"email": "charlie@example.com", "full_name": "Charlie", "password": "pass123"},
    )
    monkeypatch.setattr("app.routers.auth.pwd_context", type("", (), {"verify": lambda s, h, p: True})())
    login_response = client.post("/auth/login", json={"email": "charlie@example.com", "password": "pass123"})
    token = login_response.json()["access_token"]

    response = client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 200
    result = response.json()
    assert result["email"] == "charlie@example.com"


def test_list_accounts_returns_empty_list(client_with_db, monkeypatch):
    client, db = client_with_db

    # Register and get token
    client.post(
        "/auth/register",
        json={"email": "dave@example.com", "full_name": "Dave", "password": "pass123"},
    )
    monkeypatch.setattr("app.routers.auth.pwd_context", type("", (), {"verify": lambda s, h, p: True})())
    login_response = client.post("/auth/login", json={"email": "dave@example.com", "password": "pass123"})
    token = login_response.json()["access_token"]

    response = client.get("/accounts", headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 200
    assert response.json() == []


def test_list_transactions_returns_empty_list(client_with_db, monkeypatch):
    client, db = client_with_db

    # Register and get token
    client.post(
        "/auth/register",
        json={"email": "eve@example.com", "full_name": "Eve", "password": "pass123"},
    )
    monkeypatch.setattr("app.routers.auth.pwd_context", type("", (), {"verify": lambda s, h, p: True})())
    login_response = client.post("/auth/login", json={"email": "eve@example.com", "password": "pass123"})
    token = login_response.json()["access_token"]

    response = client.get("/transactions", headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 200
    assert response.json() == []


def test_list_budgets_returns_empty_list(client_with_db, monkeypatch):
    client, db = client_with_db

    # Register and get token
    client.post(
        "/auth/register",
        json={"email": "frank@example.com", "full_name": "Frank", "password": "pass123"},
    )
    monkeypatch.setattr("app.routers.auth.pwd_context", type("", (), {"verify": lambda s, h, p: True})())
    login_response = client.post("/auth/login", json={"email": "frank@example.com", "password": "pass123"})
    token = login_response.json()["access_token"]

    response = client.get("/budgets", headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 200
    assert response.json() == []


def test_health_check(client_with_db):
    client, _ = client_with_db
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
