from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import get_current_user
from app.models import BankAccount, Transaction, User
from app.schemas import TransactionCreate, TransactionResponse
from app.services.categorizer import categorize_transaction
from app.ws_manager import manager


router = APIRouter(prefix="/transactions", tags=["transactions"])


@router.get("", response_model=list[TransactionResponse])
def list_transactions(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return (
        db.query(Transaction)
        .filter(Transaction.user_id == current_user.id)
        .order_by(Transaction.timestamp.desc())
        .limit(300)
        .all()
    )


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

    return tx
