from sqlalchemy import Column, Integer, String, Boolean, DateTime, Float, ForeignKey
from sqlalchemy.orm import relationship
from backend.database import Base

class Vehicle(Base):
    __tablename__ = "vehicles"
    id = Column(Integer, primary_key=True)
    plate = Column(String, unique=True, nullable=False)
    owner_name = Column(String, nullable=False)
    roll_number = Column(String, default="")
    vehicle_type = Column(String, default="")
    active = Column(Boolean, default=True)
    logs = relationship("Log", back_populates="vehicle")

class Log(Base):
    __tablename__ = "logs"
    id = Column(Integer, primary_key=True)
    plate = Column(String, nullable=False, index=True)  # raw OCR value at scan time; may differ from Vehicle.plate if plate is later corrected — intentional scan record
    owner_id = Column(Integer, ForeignKey("vehicles.id"), nullable=True)
    timestamp = Column(DateTime(timezone=True), nullable=False, index=True)
    direction = Column(String, nullable=False)
    method = Column(String, default="ANPR")
    confidence_score = Column(Float, nullable=True)
    anomaly = Column(Boolean, default=False)
    vehicle = relationship("Vehicle", back_populates="logs")

class Alert(Base):
    __tablename__ = "alerts"
    id = Column(Integer, primary_key=True)
    plate = Column(String, nullable=False)
    timestamp = Column(DateTime(timezone=True), nullable=False, index=True)
    snapshot_path = Column(String, nullable=False)
    resolved = Column(Boolean, default=False, index=True)
