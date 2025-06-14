from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from datetime import datetime
from typing import Optional
import csv, io
from backend.database import get_db
from backend import crud, schemas

router = APIRouter(prefix="/logs", tags=["logs"])

def _csv_safe(val) -> str:
    s = str(val) if val is not None else ""
    if s and s[0] in ('=', '+', '-', '@', '\t', '\r'):
        return "'" + s
    return s

@router.get("/export")
def export_logs(
    plate: Optional[str] = None,
    from_dt: Optional[datetime] = None,
    to_dt: Optional[datetime] = None,
    anomaly: Optional[bool] = None,
    db: Session = Depends(get_db),
):
    logs = crud.list_logs(db, plate=plate, from_dt=from_dt, to_dt=to_dt, anomaly=anomaly)
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["id", "plate", "owner_id", "timestamp", "direction",
                     "method", "confidence_score", "anomaly"])
    for log in logs:
        writer.writerow([
            log.id,
            _csv_safe(log.plate),
            log.owner_id,
            log.timestamp,
            _csv_safe(log.direction),
            _csv_safe(log.method),
            log.confidence_score,
            log.anomaly,
        ])
    output.seek(0)
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=logs.csv"},
    )

@router.get("/", response_model=list[schemas.LogOut])
def list_logs(
    plate: Optional[str] = None,
    from_dt: Optional[datetime] = None,
    to_dt: Optional[datetime] = None,
    anomaly: Optional[bool] = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
):
    return crud.list_logs(db, plate=plate, from_dt=from_dt, to_dt=to_dt, anomaly=anomaly, skip=skip, limit=limit)
