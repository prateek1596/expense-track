from io import BytesIO
from datetime import datetime

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
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
