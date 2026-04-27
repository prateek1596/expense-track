from datetime import datetime

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models import Budget, Transaction


async def evaluate_and_notify_budget(db: Session, user_id: int, category: str, timestamp: datetime, broadcaster):
    month = timestamp.month
    year = timestamp.year
    budget = (
        db.query(Budget)
        .filter(Budget.user_id == user_id, Budget.category == category, Budget.month == month, Budget.year == year)
        .first()
    )
    if not budget:
        return

    spent = (
        db.query(func.sum(Transaction.amount))
        .filter(
            Transaction.user_id == user_id,
            Transaction.category == category,
            Transaction.tx_type == "debit",
            func.extract("month", Transaction.timestamp) == month,
            func.extract("year", Transaction.timestamp) == year,
        )
        .scalar()
        or 0.0
    )

    if float(spent) > float(budget.monthly_limit):
        over_by = float(spent) - float(budget.monthly_limit)
        percent = (float(spent) / float(budget.monthly_limit)) * 100 if budget.monthly_limit else 0
        await broadcaster(
            user_id,
            {
                "type": "budget.alert",
                "data": {
                    "category": category,
                    "month": month,
                    "year": year,
                    "limit": float(budget.monthly_limit),
                    "spent": float(spent),
                    "over_by": round(over_by, 2),
                    "percent": round(percent, 2),
                },
            },
        )
