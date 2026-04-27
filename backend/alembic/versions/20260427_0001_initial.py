"""initial schema

Revision ID: 20260427_0001
Revises:
Create Date: 2026-04-27 22:55:00
"""

from alembic import op
import sqlalchemy as sa


revision = "20260427_0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    existing_tables = set(inspector.get_table_names())

    if "users" not in existing_tables:
        op.create_table(
            "users",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("email", sa.String(length=255), nullable=False),
            sa.Column("full_name", sa.String(length=255), nullable=False),
            sa.Column("hashed_password", sa.String(length=255), nullable=False),
            sa.Column("created_at", sa.DateTime(), nullable=False),
            sa.PrimaryKeyConstraint("id"),
        )
        op.create_index(op.f("ix_users_email"), "users", ["email"], unique=True)
        op.create_index(op.f("ix_users_id"), "users", ["id"], unique=False)

    if "bank_accounts" not in existing_tables:
        op.create_table(
            "bank_accounts",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("user_id", sa.Integer(), nullable=False),
            sa.Column("bank_name", sa.String(length=120), nullable=False),
            sa.Column("masked_account", sa.String(length=32), nullable=False),
            sa.Column("aa_consent_id", sa.String(length=120), nullable=False),
            sa.Column("linked_at", sa.DateTime(), nullable=False),
            sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
            sa.PrimaryKeyConstraint("id"),
        )
        op.create_index(op.f("ix_bank_accounts_id"), "bank_accounts", ["id"], unique=False)
        op.create_index(op.f("ix_bank_accounts_user_id"), "bank_accounts", ["user_id"], unique=False)

    if "transactions" not in existing_tables:
        op.create_table(
            "transactions",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("user_id", sa.Integer(), nullable=False),
            sa.Column("account_id", sa.Integer(), nullable=False),
            sa.Column("amount", sa.Float(), nullable=False),
            sa.Column("tx_type", sa.String(length=16), nullable=False),
            sa.Column("merchant", sa.String(length=255), nullable=False),
            sa.Column("category", sa.String(length=64), nullable=False),
            sa.Column("description", sa.String(length=1024), nullable=False),
            sa.Column("timestamp", sa.DateTime(), nullable=False),
            sa.Column("raw_data", sa.JSON(), nullable=False),
            sa.ForeignKeyConstraint(["account_id"], ["bank_accounts.id"]),
            sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
            sa.PrimaryKeyConstraint("id"),
        )
        op.create_index(op.f("ix_transactions_account_id"), "transactions", ["account_id"], unique=False)
        op.create_index(op.f("ix_transactions_id"), "transactions", ["id"], unique=False)
        op.create_index(op.f("ix_transactions_timestamp"), "transactions", ["timestamp"], unique=False)
        op.create_index(op.f("ix_transactions_user_id"), "transactions", ["user_id"], unique=False)

    if "budgets" not in existing_tables:
        op.create_table(
            "budgets",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("user_id", sa.Integer(), nullable=False),
            sa.Column("category", sa.String(length=64), nullable=False),
            sa.Column("monthly_limit", sa.Float(), nullable=False),
            sa.Column("month", sa.Integer(), nullable=False),
            sa.Column("year", sa.Integer(), nullable=False),
            sa.Column("created_at", sa.DateTime(), nullable=False),
            sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
            sa.PrimaryKeyConstraint("id"),
        )
        op.create_index(op.f("ix_budgets_category"), "budgets", ["category"], unique=False)
        op.create_index(op.f("ix_budgets_id"), "budgets", ["id"], unique=False)
        op.create_index(op.f("ix_budgets_month"), "budgets", ["month"], unique=False)
        op.create_index(op.f("ix_budgets_user_id"), "budgets", ["user_id"], unique=False)
        op.create_index(op.f("ix_budgets_year"), "budgets", ["year"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_budgets_year"), table_name="budgets")
    op.drop_index(op.f("ix_budgets_user_id"), table_name="budgets")
    op.drop_index(op.f("ix_budgets_month"), table_name="budgets")
    op.drop_index(op.f("ix_budgets_id"), table_name="budgets")
    op.drop_index(op.f("ix_budgets_category"), table_name="budgets")
    op.drop_table("budgets")

    op.drop_index(op.f("ix_transactions_user_id"), table_name="transactions")
    op.drop_index(op.f("ix_transactions_timestamp"), table_name="transactions")
    op.drop_index(op.f("ix_transactions_id"), table_name="transactions")
    op.drop_index(op.f("ix_transactions_account_id"), table_name="transactions")
    op.drop_table("transactions")

    op.drop_index(op.f("ix_bank_accounts_user_id"), table_name="bank_accounts")
    op.drop_index(op.f("ix_bank_accounts_id"), table_name="bank_accounts")
    op.drop_table("bank_accounts")

    op.drop_index(op.f("ix_users_id"), table_name="users")
    op.drop_index(op.f("ix_users_email"), table_name="users")
    op.drop_table("users")
