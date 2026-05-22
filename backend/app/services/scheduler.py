from datetime import datetime, timedelta
import os
from typing import Optional

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from sqlalchemy.orm import Session

from app.config import settings
from app.models import ScheduledExport, User
from app.routers import reports as reports_router
from app.database import SessionLocal

scheduler: Optional[BackgroundScheduler] = None


def _ensure_exports_dir():
    os.makedirs(settings.exports_folder, exist_ok=True)


def _run_export_job(schedule_id: int):
    db: Session = SessionLocal()
    try:
        sched = db.query(ScheduledExport).filter(ScheduledExport.id == schedule_id, ScheduledExport.active == True).first()
        if not sched:
            return

        user = db.query(User).filter(User.id == sched.user_id).first()
        if not user:
            return

        # determine report month/year — export previous month
        now = datetime.utcnow()
        export_month = (now.month - 1) or 12
        export_year = now.year if now.month > 1 else now.year - 1

        _ensure_exports_dir()

        if sched.export_type in ("pdf", "both"):
            filename = f"scheduled-{sched.id}-monthly-{export_year}-{export_month:02d}.pdf"
            outpath = os.path.join(settings.exports_folder, filename)
            reports_router.generate_monthly_report_pdf_file(export_month, export_year, user, db, outpath)

        if sched.export_type in ("csv", "both"):
            filename = f"scheduled-{sched.id}-monthly-{export_year}-{export_month:02d}.csv"
            outpath = os.path.join(settings.exports_folder, filename)
            reports_router.generate_monthly_report_csv_file(export_month, export_year, user, db, outpath)

        sched.last_run_at = datetime.utcnow()
        db.commit()
    finally:
        db.close()


def init_scheduler(app=None):
    global scheduler
    if scheduler is not None:
        return scheduler
    scheduler = BackgroundScheduler()

    # load schedules from DB
    db: Session = SessionLocal()
    try:
        schedules = db.query(ScheduledExport).filter(ScheduledExport.active == True).all()
        for sched in schedules:
            trigger = CronTrigger(day=sched.day_of_month, hour=sched.hour, minute=sched.minute)
            scheduler.add_job(_run_export_job, trigger, args=[sched.id], id=f"scheduled_export_{sched.id}")
    finally:
        db.close()

    scheduler.start()
    return scheduler


def schedule_new(sched: ScheduledExport):
    global scheduler
    if scheduler is None:
        init_scheduler()
    trigger = CronTrigger(day=sched.day_of_month, hour=sched.hour, minute=sched.minute)
    scheduler.add_job(_run_export_job, trigger, args=[sched.id], id=f"scheduled_export_{sched.id}")


def remove_schedule(sched_id: int):
    global scheduler
    if scheduler is None:
        return
    job_id = f"scheduled_export_{sched_id}"
    try:
        scheduler.remove_job(job_id)
    except Exception:
        pass
