from datetime import datetime

from fastapi import APIRouter, Depends, Header, HTTPException, status
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.models import BankAccount, Transaction
from app.services.categorizer import categorize_transaction
from app.ws_manager import manager


router = APIRouter(prefix="/webhooks", tags=["webhooks"])


@router.post("/setu")
async def setu_webhook(payload: dict, db: Session = Depends(get_db), x_webhook_secret: str | None = Header(default=None)):
    if settings.setu_webhook_secret and x_webhook_secret != settings.setu_webhook_secret:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid webhook signature")

    account_id = payload.get("account_id")
    transactions = payload.get("transactions", [])
    if not account_id:
        raise HTTPException(status_code=400, detail="account_id is required")

    account = db.query(BankAccount).filter(BankAccount.id == account_id).first()
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")

    created = 0
    for item in transactions:
        merchant = item.get("merchant", "Unknown")
        description = item.get("description", "")
        timestamp = item.get("timestamp")
        tx = Transaction(
            user_id=account.user_id,
            account_id=account.id,
            amount=float(item.get("amount", 0)),
            tx_type=item.get("tx_type", "debit"),
            merchant=merchant,
            category=categorize_transaction(merchant, description),
            description=description,
            timestamp=datetime.fromisoformat(timestamp) if timestamp else datetime.utcnow(),
            raw_data=item,
        )
        db.add(tx)
        created += 1

    db.commit()

    await manager.broadcast_to_user(
        account.user_id,
        {
            "type": "transaction.batch_created",
            "count": created,
        },
    )

    return {"status": "ok", "created": created}
