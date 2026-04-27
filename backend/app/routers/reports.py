from datetime import datetime

from fastapi import APIRouter, Depends
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import get_current_user
from app.models import Transaction, User
from app.schemas import MonthlyCategoryReportItem, MonthlyReportResponse


router = APIRouter(prefix="/reports", tags=["reports"])


@router.get("/monthly", response_model=MonthlyReportResponse)
def monthly_report(
    month: int,
    year: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    start = datetime(year, month, 1)
    end = datetime(year + (month // 12), (month % 12) + 1, 1)

    rows = (
        db.query(Transaction.category, func.sum(Transaction.amount).label("total"))
        .filter(
            Transaction.user_id == current_user.id,
            Transaction.tx_type == "debit",
            Transaction.timestamp >= start,
            Transaction.timestamp < end,
        )
        .group_by(Transaction.category)
        .all()
    )

    by_category = [MonthlyCategoryReportItem(category=row[0], total=float(row[1] or 0)) for row in rows]
    total_spend = float(sum(item.total for item in by_category))

    return MonthlyReportResponse(
        month=month,
        year=year,
        total_spend=total_spend,
        by_category=by_category,
    )
