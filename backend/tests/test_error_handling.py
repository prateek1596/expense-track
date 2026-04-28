import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base, get_db
from app.main import app
from app.models import User, BankAccount, Budget
from app.security import create_access_token


@pytest.fixture(scope="function")
def test_db():
    """Create in-memory SQLite database for testing with thread safety."""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()

    yield session

    session.close()
    engine.dispose()


@pytest.fixture
def client(test_db):
    """Create test client with test database override."""
    app.dependency_overrides[get_db] = lambda: test_db

    try:
        yield TestClient(app)
    finally:
        app.dependency_overrides.clear()


@pytest.fixture
def auth_token(client, test_db):
    """Create authenticated user and return auth token."""
    user = User(
        email="testuser@example.com",
        full_name="Test User",
        hashed_password="hashed_password",
    )
    test_db.add(user)
    test_db.commit()
    test_db.refresh(user)

    token = create_access_token(str(user.id))
    return token, user


# =================
# Error Handling Tests
# =================

def test_auth_me_missing_token(client):
    """Test /auth/me endpoint without authorization header."""
    response = client.get("/auth/me")
    assert response.status_code in [401, 403]


def test_auth_me_invalid_token(client):
    """Test /auth/me endpoint with invalid token."""
    response = client.get(
        "/auth/me",
        headers={"Authorization": "Bearer invalid_token_format"},
    )
    assert response.status_code in [401, 403]


def test_list_accounts_missing_auth(client):
    """Test /accounts endpoint without authentication."""
    response = client.get("/accounts")
    assert response.status_code in [401, 403]


def test_list_accounts_invalid_token(client):
    """Test /accounts endpoint with invalid token."""
    response = client.get(
        "/accounts",
        headers={"Authorization": "Bearer invalid_token"},
    )
    assert response.status_code in [401, 403]


def test_list_transactions_missing_auth(client):
    """Test /transactions endpoint without authentication."""
    response = client.get("/transactions")
    assert response.status_code in [401, 403]


def test_list_transactions_invalid_token(client):
    """Test /transactions endpoint with invalid token."""
    response = client.get(
        "/transactions",
        headers={"Authorization": "Bearer invalid_token"},
    )
    assert response.status_code in [401, 403]


def test_create_transaction_missing_auth(client):
    """Test POST /transactions without authentication."""
    response = client.post(
        "/transactions",
        json={
            "account_id": "test",
            "amount": 100,
            "tx_type": "debit",
            "merchant": "Test",
            "description": "Test",
        },
    )
    assert response.status_code in [401, 403]


def test_register_invalid_email_format(client):
    """Test registration with invalid email."""
    response = client.post(
        "/auth/register",
        json={
            "email": "invalid-email",
            "full_name": "Test User",
            "password": "password123",
        },
    )
    # Should fail validation or return 400
    assert response.status_code >= 400


def test_register_missing_required_fields(client):
    """Test registration with missing required fields."""
    response = client.post(
        "/auth/register",
        json={"email": "test@example.com"},
    )
    assert response.status_code == 422  # Validation error


def test_register_empty_password(client):
    """Test registration with empty password."""
    response = client.post(
        "/auth/register",
        json={
            "email": "test@example.com",
            "full_name": "Test User",
            "password": "",
        },
    )
    assert response.status_code >= 400


def test_login_nonexistent_user(client):
    """Test login with non-existent user."""
    response = client.post(
        "/auth/login",
        json={
            "email": "nonexistent@example.com",
            "password": "password123",
        },
    )
    assert response.status_code == 401


def test_login_missing_email(client):
    """Test login with missing email."""
    response = client.post(
        "/auth/login",
        json={"password": "password123"},
    )
    assert response.status_code == 422


def test_login_missing_password(client):
    """Test login with missing password."""
    response = client.post(
        "/auth/login",
        json={"email": "test@example.com"},
    )
    assert response.status_code == 422


def test_budget_operations_require_auth(client):
    """Test budget endpoints require authentication."""
    response = client.get("/budgets")
    assert response.status_code in [401, 403]


def test_health_check_no_auth(client):
    """Test health check endpoint (should not require auth)."""
    response = client.get("/health")
    assert response.status_code == 200
    assert "status" in response.json()


# =================
# Success Case Tests
# =================

def test_list_budgets_empty(client, auth_token):
    """Test listing budgets when none exist."""
    token, _ = auth_token
    response = client.get(
        "/budgets",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    assert response.json() == []


def test_list_budgets_with_data(client, auth_token, test_db):
    """Test listing budgets with data."""
    token, user = auth_token

    budget = Budget(
        user_id=user.id,
        category="Food",
        limit=500.0,
        current_spend=150.0,
    )
    test_db.add(budget)
    test_db.commit()

    response = client.get(
        "/budgets",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["category"] == "Food"
    assert data[0]["limit"] == 500.0
