from datetime import datetime

from sqlalchemy import JSON, DateTime, Float, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    accounts: Mapped[list["BankAccount"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    transactions: Mapped[list["Transaction"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    budgets: Mapped[list["Budget"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    scheduled_exports: Mapped[list["ScheduledExport"]] = relationship(back_populates="user", cascade="all, delete-orphan")


class BankAccount(Base):
    __tablename__ = "bank_accounts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    bank_name: Mapped[str] = mapped_column(String(120), nullable=False)
    masked_account: Mapped[str] = mapped_column(String(32), nullable=False)
    aa_consent_id: Mapped[str] = mapped_column(String(120), nullable=False)
    linked_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    user: Mapped[User] = relationship(back_populates="accounts")
    transactions: Mapped[list["Transaction"]] = relationship(back_populates="account", cascade="all, delete-orphan")


class Transaction(Base):
    __tablename__ = "transactions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    account_id: Mapped[int] = mapped_column(ForeignKey("bank_accounts.id"), nullable=False, index=True)
    amount: Mapped[float] = mapped_column(Float, nullable=False)
    tx_type: Mapped[str] = mapped_column(String(16), nullable=False)
    merchant: Mapped[str] = mapped_column(String(255), nullable=False)
    category: Mapped[str] = mapped_column(String(64), nullable=False, default="Other")
    description: Mapped[str] = mapped_column(String(1024), nullable=False)
    timestamp: Mapped[datetime] = mapped_column(DateTime, nullable=False, index=True)
    raw_data: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)

    user: Mapped[User] = relationship(back_populates="transactions")
    account: Mapped[BankAccount] = relationship(back_populates="transactions")


class Budget(Base):
    __tablename__ = "budgets"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    category: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    monthly_limit: Mapped[float] = mapped_column(Float, nullable=False)
    month: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    year: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    user: Mapped[User] = relationship(back_populates="budgets")


class ScheduledExport(Base):
    __tablename__ = "scheduled_exports"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    export_type: Mapped[str] = mapped_column(String(16), nullable=False)  # 'csv', 'pdf', or 'both'
    day_of_month: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    hour: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    minute: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    active: Mapped[bool] = mapped_column(String(5), nullable=False, default="true")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    last_run_at: Mapped[datetime] = mapped_column(DateTime, default=None, nullable=True)

    user: Mapped[User] = relationship(back_populates="scheduled_exports")
