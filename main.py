import threading
import uvicorn
from anpr_engine.engine import run_engine
from backend.main import app
from backend.database import create_tables

def start_api():
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")

if __name__ == "__main__":
    create_tables()
    api_thread = threading.Thread(target=start_api, daemon=True)
    api_thread.start()
    print("API started on http://0.0.0.0:8000")
    print("Starting ANPR engine...")
    run_engine()
