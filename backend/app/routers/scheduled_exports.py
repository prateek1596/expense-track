from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import get_current_user
from app.models import ScheduledExport, User
from app.services import scheduler as scheduler_service

router = APIRouter(prefix="/exports", tags=["exports"])


@router.get("/schedules")
def list_schedules(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    rows = db.query(ScheduledExport).filter(ScheduledExport.user_id == current_user.id).all()
    return [
        {
            "id": r.id,
            "export_type": r.export_type,
            "day_of_month": r.day_of_month,
            "hour": r.hour,
            "minute": r.minute,
            "active": r.active,
            "last_run_at": r.last_run_at,
        }
        for r in rows
    ]


@router.post("/schedules")
def create_schedule(payload: dict, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    # expected payload: {export_type, day_of_month, hour, minute}
    export_type = payload.get("export_type")
    if export_type not in ("csv", "pdf", "both"):
        raise HTTPException(status_code=400, detail="export_type must be 'csv', 'pdf' or 'both'")
    day = int(payload.get("day_of_month", 1))
    hour = int(payload.get("hour", 0))
    minute = int(payload.get("minute", 0))

    sched = ScheduledExport(
        user_id=current_user.id,
        export_type=export_type,
        day_of_month=day,
        hour=hour,
        minute=minute,
        active=True,
        created_at=datetime.utcnow(),
    )
    db.add(sched)
    db.commit()
    db.refresh(sched)

    # schedule job in running scheduler if available
    try:
        scheduler_service.schedule_new(sched)
    except Exception:
        # scheduler may not be running in tests/dev environment
        pass

    return {"id": sched.id}


@router.delete("/schedules/{schedule_id}")
def delete_schedule(schedule_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    sched = db.query(ScheduledExport).filter(ScheduledExport.id == schedule_id, ScheduledExport.user_id == current_user.id).first()
    if not sched:
        raise HTTPException(status_code=404, detail="Not found")
    db.delete(sched)
    db.commit()
    try:
        scheduler_service.remove_schedule(schedule_id)
    except Exception:
        pass
    return {"ok": True}
