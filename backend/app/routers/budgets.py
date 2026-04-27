from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import get_current_user
from app.models import Budget, User
from app.schemas import BudgetCreateRequest, BudgetResponse


router = APIRouter(prefix="/budgets", tags=["budgets"])


@router.get("", response_model=list[BudgetResponse])
def list_budgets(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return db.query(Budget).filter(Budget.user_id == current_user.id).order_by(Budget.year.desc(), Budget.month.desc()).all()


@router.post("", response_model=BudgetResponse, status_code=status.HTTP_201_CREATED)
def upsert_budget(payload: BudgetCreateRequest, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    budget = (
        db.query(Budget)
        .filter(
            Budget.user_id == current_user.id,
            Budget.category == payload.category,
            Budget.month == payload.month,
            Budget.year == payload.year,
        )
        .first()
    )
    if budget:
        budget.monthly_limit = payload.monthly_limit
    else:
        budget = Budget(
            user_id=current_user.id,
            category=payload.category,
            monthly_limit=payload.monthly_limit,
            month=payload.month,
            year=payload.year,
        )
        db.add(budget)

    db.commit()
    db.refresh(budget)
    return budget
