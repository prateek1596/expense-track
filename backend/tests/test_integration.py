import asyncio
from datetime import datetime
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base, get_db
from app.main import app
from app.models import User, BankAccount, Transaction
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
    """Register a test user and return an auth token."""
    # Create user in database with mocked password hashing
    with patch("app.security.get_password_hash") as mock_hash:
        mock_hash.return_value = "hashed_testpass123"
        user = User(
            email="testuser@example.com",
            full_name="Test User",
            hashed_password="hashed_testpass123",
        )
        test_db.add(user)
        test_db.commit()
        test_db.refresh(user)

    # Return token (manually created using the user ID)
    token = create_access_token(str(user.id))
    return token, user


# Auth Tests
def test_register_new_user(client, test_db):
    response = client.post(
        "/auth/register",
        json={
            "email": "newuser@example.com",
            "full_name": "New User",
            "password": "securepass123",
        },
    )

    assert response.status_code == 201
    data = response.json()
    assert data["email"] == "newuser@example.com"
    assert data["full_name"] == "New User"

    # Verify user was created in DB
    user = test_db.query(User).filter(User.email == "newuser@example.com").first()
    assert user is not None


def test_register_duplicate_email(client, test_db):
    # Create first user with mocked password hashing
    with patch("app.security.get_password_hash") as mock_hash:
        mock_hash.return_value = "hashed_pass123"
        user = User(
            email="duplicate@example.com",
            full_name="First User",
            hashed_password="hashed_pass123",
        )
        test_db.add(user)
        test_db.commit()

    # Try to register with same email
    response = client.post(
        "/auth/register",
        json={
            "email": "duplicate@example.com",
            "full_name": "Second User",
            "password": "pass123",
        },
    )

    assert response.status_code == 400
    assert "already registered" in response.json()["detail"]


def test_login_valid_credentials(client, test_db):
    # Create user with mocked password hashing
    with patch("app.security.get_password_hash") as mock_hash:
        mock_hash.return_value = "hashed_correctpass"
        user = User(
            email="login@example.com",
            full_name="Login User",
            hashed_password="hashed_correctpass",
        )
        test_db.add(user)
        test_db.commit()

    # Mock the verify_password function to return True for test
    with patch("app.security.verify_password") as mock_verify:
        mock_verify.return_value = True
        response = client.post(
            "/auth/login",
            json={"email": "login@example.com", "password": "correctpass"},
        )

    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"


def test_login_invalid_credentials(client, test_db):
    # Create user with mocked password hashing
    with patch("app.security.get_password_hash") as mock_hash:
        mock_hash.return_value = "hashed_correctpass"
        user = User(
            email="wrongpass@example.com",
            full_name="Wrong Pass User",
            hashed_password="hashed_correctpass",
        )
        test_db.add(user)
        test_db.commit()

    # Mock verify_password to return False
    with patch("app.security.verify_password") as mock_verify:
        mock_verify.return_value = False
        response = client.post(
            "/auth/login",
            json={"email": "wrongpass@example.com", "password": "wrongpass"},
        )

    assert response.status_code == 401
    assert "Invalid credentials" in response.json()["detail"]


def test_me_endpoint(client, auth_token):
    token, user = auth_token

    response = client.get(
        "/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "testuser@example.com"
    assert data["full_name"] == "Test User"


def test_me_without_token(client):
    response = client.get("/auth/me")

    assert response.status_code == 403


# Account Tests
def test_list_accounts_empty(client, auth_token):
    token, _ = auth_token

    response = client.get(
        "/accounts",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    assert response.json() == []


def test_list_accounts_with_data(client, auth_token, test_db):
    token, user = auth_token

    # Create accounts
    account1 = BankAccount(
        user_id=user.id,
        bank_name="HDFC",
        masked_account="XXXX1234",
        aa_consent_id="consent-1",
    )
    account2 = BankAccount(
        user_id=user.id,
        bank_name="ICICI",
        masked_account="XXXX5678",
        aa_consent_id="consent-2",
    )
    test_db.add_all([account1, account2])
    test_db.commit()

    response = client.get(
        "/accounts",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    assert data[0]["bank_name"] in ["HDFC", "ICICI"]


# Transaction Tests
def test_list_transactions_empty(client, auth_token):
    token, _ = auth_token

    response = client.get(
        "/transactions",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    assert response.json() == []


def test_list_transactions_with_data(client, auth_token, test_db):
    token, user = auth_token

    # Create account and transactions
    account = BankAccount(
        user_id=user.id,
        bank_name="HDFC",
        masked_account="XXXX1234",
        aa_consent_id="consent-1",
    )
    test_db.add(account)
    test_db.commit()

    tx1 = Transaction(
        user_id=user.id,
        account_id=account.id,
        amount=100.0,
        tx_type="debit",
        merchant="Swiggy",
        category="Food",
        description="Dinner",
        timestamp=datetime.utcnow(),
        raw_data={},
    )
    tx2 = Transaction(
        user_id=user.id,
        account_id=account.id,
        amount=50.0,
        tx_type="debit",
        merchant="Amazon",
        category="Shopping",
        description="Book",
        timestamp=datetime.utcnow(),
        raw_data={},
    )
    test_db.add_all([tx1, tx2])
    test_db.commit()

    response = client.get(
        "/transactions",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    assert data[0]["merchant"] in ["Swiggy", "Amazon"]


def test_health_check(client):
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
