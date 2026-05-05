from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import get_current_user
from app.models import BankAccount, Transaction, User
from app.schemas import TransactionCreate, TransactionResponse
from app.services.budget_alerts import evaluate_and_notify_budget
from app.services.categorizer import categorize_transaction
from app.ws_manager import manager


router = APIRouter(prefix="/transactions", tags=["transactions"])


@router.get("", response_model=list[TransactionResponse])
def list_transactions(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    month: int | None = Query(default=None, ge=1, le=12),
    year: int | None = Query(default=None, ge=1),
    category: str | None = Query(default=None),
    search: str | None = Query(default=None),
    account_id: int | None = Query(default=None, ge=1),
):
    query = db.query(Transaction).filter(Transaction.user_id == current_user.id)

    if account_id is not None:
        query = query.filter(Transaction.account_id == account_id)

    if category:
        query = query.filter(Transaction.category == category)

    if search:
        pattern = f"%{search.strip()}%"
        query = query.filter(or_(Transaction.merchant.ilike(pattern), Transaction.description.ilike(pattern)))

    if month is not None and year is not None:
        start = datetime(year, month, 1)
        end = datetime(year + (month // 12), (month % 12) + 1, 1)
        query = query.filter(Transaction.timestamp >= start, Transaction.timestamp < end)

    return query.order_by(Transaction.timestamp.desc()).limit(300).all()


@router.post("", response_model=TransactionResponse, status_code=status.HTTP_201_CREATED)
async def create_transaction(payload: TransactionCreate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    account = (
        db.query(BankAccount)
        .filter(BankAccount.id == payload.account_id, BankAccount.user_id == current_user.id)
        .first()
    )
    if not account:
        raise HTTPException(status_code=404, detail="Bank account not found")

    category = categorize_transaction(payload.merchant, payload.description)

    tx = Transaction(
        user_id=current_user.id,
        account_id=payload.account_id,
        amount=payload.amount,
        tx_type=payload.tx_type,
        merchant=payload.merchant,
        category=category,
        description=payload.description,
        timestamp=payload.timestamp,
        raw_data=payload.raw_data,
    )
    db.add(tx)
    db.commit()
    db.refresh(tx)

    await manager.broadcast_to_user(
        current_user.id,
        {
            "type": "transaction.created",
            "data": {
                "id": tx.id,
                "amount": tx.amount,
                "tx_type": tx.tx_type,
                "merchant": tx.merchant,
                "category": tx.category,
                "description": tx.description,
                "timestamp": tx.timestamp.isoformat(),
                "account_id": tx.account_id,
            },
        },
    )

    await evaluate_and_notify_budget(db, current_user.id, tx.category, tx.timestamp, manager.broadcast_to_user)

    return tx
