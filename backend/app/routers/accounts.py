from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import get_current_user
from app.models import BankAccount, User
from app.schemas import BankAccountResponse, LinkBankRequest, LinkBankResponse
from app.services.setu_client import SetuClientError, create_consent


router = APIRouter(prefix="/accounts", tags=["accounts"])


@router.get("", response_model=list[BankAccountResponse])
def list_accounts(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return db.query(BankAccount).filter(BankAccount.user_id == current_user.id).all()


@router.post("/link", response_model=LinkBankResponse, status_code=status.HTTP_201_CREATED)
async def link_account(payload: LinkBankRequest, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    try:
        consent = await create_consent(payload.bank_name, payload.masked_account, current_user.id)
    except SetuClientError as exc:
        raise HTTPException(status_code=502, detail=str(exc))

    account = BankAccount(
        user_id=current_user.id,
        bank_name=payload.bank_name,
        masked_account=payload.masked_account,
        aa_consent_id=consent["consent_id"],
    )
    db.add(account)
    db.commit()
    db.refresh(account)

    return {
        "account": BankAccountResponse.model_validate(account),
        "consent_url": consent["consent_url"],
    }
