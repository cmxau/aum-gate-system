from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Optional
from backend.database import get_db
from backend import crud, schemas

router = APIRouter(prefix="/alerts", tags=["alerts"])

@router.get("/", response_model=list[schemas.AlertOut])
def list_alerts(resolved: Optional[bool] = None, skip: int = 0, limit: int = 100,
                db: Session = Depends(get_db)):
    return crud.list_alerts(db, resolved=resolved, skip=skip, limit=limit)

@router.post("/{alert_id}/resolve")
def resolve_alert(alert_id: int, db: Session = Depends(get_db)):
    if not crud.resolve_alert(db, alert_id):
        raise HTTPException(404, "Alert not found")
    return {"ok": True}
