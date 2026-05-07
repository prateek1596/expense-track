import hashlib
import hmac
from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.models import BankAccount, Transaction
from app.services.budget_alerts import evaluate_and_notify_budget
from app.services.categorizer import categorize_transaction
from app.ws_manager import manager


router = APIRouter(prefix="/webhooks", tags=["webhooks"])


def _verify_signature(secret: str, raw_body: bytes, received_signature: str) -> bool:
    computed = hmac.new(secret.encode("utf-8"), raw_body, hashlib.sha256).hexdigest()
    prefixed = f"sha256={computed}"
    return hmac.compare_digest(received_signature, computed) or hmac.compare_digest(received_signature, prefixed)


@router.post("/setu")
async def setu_webhook(request: Request, db: Session = Depends(get_db)):
    raw_body = await request.body()
    payload = await request.json()

    if settings.setu_webhook_secret:
        signature_header_name = settings.setu_webhook_signature_header.lower()
        received_signature = request.headers.get(signature_header_name)
        legacy_header = request.headers.get("x-webhook-secret")
        if legacy_header == settings.setu_webhook_secret:
            received_signature = settings.setu_webhook_secret

        if not received_signature:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing webhook signature")

        if legacy_header != settings.setu_webhook_secret and not _verify_signature(settings.setu_webhook_secret, raw_body, received_signature):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid webhook signature")

    account_id = payload.get("account_id")
    transactions = payload.get("transactions", [])
    if not account_id:
        raise HTTPException(status_code=400, detail="account_id is required")

    account = db.query(BankAccount).filter(BankAccount.id == account_id).first()
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")

    created = 0
    touched_categories: set[tuple[str, datetime]] = set()
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
            timestamp=datetime.fromisoformat(timestamp) if timestamp else datetime.now(UTC),
            raw_data=item,
        )
        db.add(tx)
        created += 1
        touched_categories.add((tx.category, tx.timestamp))

    db.commit()

    for category, timestamp in touched_categories:
        await evaluate_and_notify_budget(db, account.user_id, category, timestamp, manager.broadcast_to_user)

    await manager.broadcast_to_user(
        account.user_id,
        {
            "type": "transaction.batch_created",
            "count": created,
        },
    )

    return {"status": "ok", "created": created}
