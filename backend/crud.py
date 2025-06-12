from sqlalchemy.orm import Session
from datetime import datetime, timezone
from typing import Literal
from backend.models import Vehicle, Log, Alert
from backend.schemas import VehicleCreate, VehicleUpdate

def get_vehicle_by_plate(db: Session, plate: str) -> Vehicle | None:
    return db.query(Vehicle).filter(Vehicle.plate == plate).first()

def _like(val: str) -> str:
    return "%" + val.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_") + "%"

def list_vehicles(db: Session, search: str = None) -> list[Vehicle]:
    q = db.query(Vehicle)
    if search:
        pattern = _like(search)
        q = q.filter(
            Vehicle.plate.ilike(pattern) |
            Vehicle.owner_name.ilike(pattern) |
            Vehicle.roll_number.ilike(pattern)
        )
    return q.all()

def create_vehicle(db: Session, data: VehicleCreate) -> Vehicle:
    vehicle = Vehicle(**data.model_dump())
    db.add(vehicle)
    db.commit()
    db.refresh(vehicle)
    return vehicle

def update_vehicle(db: Session, vehicle_id: int, data: VehicleUpdate) -> Vehicle | None:
    vehicle = db.query(Vehicle).filter(Vehicle.id == vehicle_id).first()
    if not vehicle:
        return None
    for k, v in data.model_dump(exclude_unset=True).items():
        setattr(vehicle, k, v)
    db.commit()
    db.refresh(vehicle)
    return vehicle

def deactivate_vehicle(db: Session, vehicle_id: int) -> bool:
    vehicle = db.query(Vehicle).filter(Vehicle.id == vehicle_id).first()
    if not vehicle:
        return False
    vehicle.active = False
    db.commit()
    return True

def create_log(db: Session, plate: str, owner_id: int | None, direction: Literal["IN", "OUT"],
               confidence_score: float | None = None, anomaly: bool = False,
               method: str = "ANPR") -> Log:
    log = Log(plate=plate, owner_id=owner_id, direction=direction,
              confidence_score=confidence_score, anomaly=anomaly, method=method,
              timestamp=datetime.now(timezone.utc))
    db.add(log)
    db.commit()
    db.refresh(log)
    return log

def is_double_entry(db: Session, plate: str) -> bool:
    last = db.query(Log).filter(Log.plate == plate).order_by(Log.timestamp.desc()).first()
    return last is not None and last.direction == "IN"

def list_logs(db: Session, plate: str = None, from_dt: datetime = None,
              to_dt: datetime = None, anomaly: bool = None,
              skip: int = 0, limit: int = 100) -> list[Log]:
    from datetime import timezone as _tz
    q = db.query(Log)
    if plate:
        q = q.filter(Log.plate == plate)
    if from_dt:
        if from_dt.tzinfo is None:
            from_dt = from_dt.replace(tzinfo=_tz.utc)
        q = q.filter(Log.timestamp >= from_dt)
    if to_dt:
        if to_dt.tzinfo is None:
            to_dt = to_dt.replace(tzinfo=_tz.utc)
        q = q.filter(Log.timestamp <= to_dt)
    if anomaly is not None:
        q = q.filter(Log.anomaly == anomaly)
    return q.order_by(Log.timestamp.desc()).offset(skip).limit(limit).all()

def create_alert(db: Session, plate: str, snapshot_path: str) -> Alert:
    alert = Alert(plate=plate, snapshot_path=snapshot_path,
                  timestamp=datetime.now(timezone.utc))
    db.add(alert)
    db.commit()
    db.refresh(alert)
    return alert

def list_alerts(db: Session, resolved: bool = None, skip: int = 0, limit: int = 100) -> list[Alert]:
    q = db.query(Alert)
    if resolved is not None:
        q = q.filter(Alert.resolved == resolved)
    return q.order_by(Alert.timestamp.desc()).offset(skip).limit(limit).all()

def resolve_alert(db: Session, alert_id: int) -> bool:
    alert = db.query(Alert).filter(Alert.id == alert_id).first()
    if not alert:
        return False
    alert.resolved = True
    db.commit()
    return True
