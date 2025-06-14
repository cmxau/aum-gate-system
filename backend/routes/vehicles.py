from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session
import csv, io
from backend.database import get_db
from backend import crud, schemas

router = APIRouter(prefix="/vehicles", tags=["vehicles"])

@router.get("/", response_model=list[schemas.VehicleOut])
def list_vehicles(search: str = None, db: Session = Depends(get_db)):
    return crud.list_vehicles(db, search=search)

@router.post("/", response_model=schemas.VehicleOut, status_code=201)
def create_vehicle(vehicle: schemas.VehicleCreate, db: Session = Depends(get_db)):
    if crud.get_vehicle_by_plate(db, vehicle.plate):
        raise HTTPException(400, "Plate already registered")
    return crud.create_vehicle(db, vehicle)

@router.post("/import")
def import_vehicles(file: UploadFile = File(...), db: Session = Depends(get_db)):
    MAX_SIZE = 5 * 1024 * 1024  # 5 MB
    content_bytes = file.file.read(MAX_SIZE + 1)
    if len(content_bytes) > MAX_SIZE:
        raise HTTPException(413, "CSV file too large (max 5 MB)")
    content = content_bytes.decode("utf-8")
    reader = csv.DictReader(io.StringIO(content))
    imported, skipped = 0, 0
    for row in reader:
        plate = row.get("plate", "").strip().upper()
        if not plate or crud.get_vehicle_by_plate(db, plate):
            skipped += 1
            continue
        crud.create_vehicle(db, schemas.VehicleCreate(
            plate=plate,
            owner_name=row.get("owner_name", ""),
            roll_number=row.get("roll_number", ""),
            vehicle_type=row.get("vehicle_type", ""),
        ))
        imported += 1
    return {"imported": imported, "skipped": skipped}

@router.put("/{vehicle_id}", response_model=schemas.VehicleOut)
def update_vehicle(vehicle_id: int, vehicle: schemas.VehicleUpdate, db: Session = Depends(get_db)):
    result = crud.update_vehicle(db, vehicle_id, vehicle)
    if not result:
        raise HTTPException(404, "Vehicle not found")
    return result

@router.delete("/{vehicle_id}")
def deactivate_vehicle(vehicle_id: int, db: Session = Depends(get_db)):
    if not crud.deactivate_vehicle(db, vehicle_id):
        raise HTTPException(404, "Vehicle not found")
    return {"ok": True}
