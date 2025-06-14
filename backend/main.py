import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from backend.database import create_tables
from backend.routes import vehicles, logs, alerts

app = FastAPI(title="ANPR Gate System")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

@app.on_event("startup")
def startup():
    create_tables()

app.include_router(vehicles.router)
app.include_router(logs.router)
app.include_router(alerts.router)

os.makedirs("snapshots", exist_ok=True)
app.mount("/snapshots", StaticFiles(directory="snapshots"), name="snapshots")
app.mount("/", StaticFiles(directory="dashboard", html=True), name="dashboard")
