from datetime import datetime
from io import BytesIO

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import get_current_user
from app.models import Transaction, User
from app.schemas import MonthlyCategoryReportItem, MonthlyReportResponse, RecurringMerchantItem, RecurringSpendingResponse


router = APIRouter(prefix="/reports", tags=["reports"])


def _shift_month(year: int, month: int, delta: int) -> tuple[int, int]:
    index = year * 12 + (month - 1) + delta
    return index // 12, index % 12 + 1


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


@router.get("/recurring", response_model=RecurringSpendingResponse)
def recurring_spending(
    month: int,
    year: int,
    lookback_months: int = 6,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if lookback_months < 1:
        lookback_months = 1

    start_year, start_month = _shift_month(year, month, -(lookback_months - 1))
    start = datetime(start_year, start_month, 1)
    end = datetime(year + (month // 12), (month % 12) + 1, 1)

    # Normalize merchant and category to lower-case to better detect recurring merchants
    rows = (
        db.query(
            func.lower(func.trim(Transaction.merchant)).label("merchant_norm"),
            func.lower(func.trim(Transaction.category)).label("category_norm"),
            func.count(Transaction.id).label("count"),
            func.sum(Transaction.amount).label("total"),
            func.min(Transaction.timestamp).label("first_seen"),
            func.max(Transaction.timestamp).label("last_seen"),
        )
        .filter(
            Transaction.user_id == current_user.id,
            Transaction.tx_type == "debit",
            Transaction.timestamp >= start,
            Transaction.timestamp < end,
        )
        .group_by(func.lower(func.trim(Transaction.merchant)), func.lower(func.trim(Transaction.category)))
        .having(func.count(Transaction.id) > 1)
        .order_by(func.sum(Transaction.amount).desc())
        .all()
    )

    recurring_merchants = []
    for row in rows:
        # Use normalized values but present them in title-case for readability
        merchant = (row.merchant_norm or '').title()
        category = (row.category_norm or '').title()
        recurring_merchants.append(
            RecurringMerchantItem(
                merchant=merchant,
                category=category,
                count=int(row.count or 0),
                total=float(row.total or 0),
                average=float((row.total or 0) / row.count) if row.count else 0,
                first_seen=row.first_seen,
                last_seen=row.last_seen,
            )
        )

    return RecurringSpendingResponse(
        month=month,
        year=year,
        lookback_months=lookback_months,
        recurring_merchants=recurring_merchants,
    )


@router.get("/monthly/pdf")
def monthly_report_pdf(
    month: int,
    year: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    report = monthly_report(month, year, current_user, db)

    buffer = BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4
    y = height - 50

    pdf.setFont("Helvetica-Bold", 16)
    pdf.drawString(50, y, "Spend - Monthly Expense Report")
    y -= 24
    pdf.setFont("Helvetica", 12)
    pdf.drawString(50, y, f"User: {current_user.full_name} ({current_user.email})")
    y -= 18
    pdf.drawString(50, y, f"Month/Year: {month}/{year}")
    y -= 18
    pdf.drawString(50, y, f"Total Spend: INR {report.total_spend:.2f}")
    y -= 28

    pdf.setFont("Helvetica-Bold", 12)
    pdf.drawString(50, y, "Category")
    pdf.drawString(350, y, "Amount (INR)")
    y -= 14
    pdf.line(50, y, width - 50, y)
    y -= 16
    pdf.setFont("Helvetica", 11)

    for item in report.by_category:
        if y < 70:
            pdf.showPage()
            y = height - 50
            pdf.setFont("Helvetica", 11)
        pdf.drawString(50, y, item.category)
        pdf.drawString(350, y, f"{item.total:.2f}")
        y -= 16

    pdf.showPage()
    pdf.save()
    buffer.seek(0)

    filename = f"monthly-report-{year}-{month:02d}.pdf"
    return StreamingResponse(
        buffer,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


@router.get("/monthly/csv")
def monthly_report_csv(
    month: int,
    year: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Return a CSV export of the monthly category totals for the current user."""
    report = monthly_report(month, year, current_user, db)

    # Build CSV content
    out = BytesIO()
    # write header
    out.write("category,amount\r\n".encode("utf-8"))
    for item in report.by_category:
        # escape commas by quoting
        cat = '"' + (item.category or '').replace('"', '""') + '"'
        amt = f"{item.total:.2f}"
        out.write((cat + "," + amt + "\r\n").encode("utf-8"))

    out.seek(0)
    filename = f"monthly-report-{year}-{month:02d}.csv"
    return StreamingResponse(
        out,
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )
