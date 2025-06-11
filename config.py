from typing import Literal
from pydantic import SecretStr
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    camera_url: str = "rtsp://localhost:554/stream"
    confidence_threshold: float = 0.85
    gate_close_delay: int = 8
    duplicate_suppression_seconds: int = 30
    gate_direction: Literal["IN", "OUT"] = "IN"
    twilio_account_sid: SecretStr = SecretStr("")
    twilio_auth_token: SecretStr = SecretStr("")
    twilio_from_number: SecretStr = SecretStr("")
    guard_phone_number: str = ""
    snapshot_dir: str = "snapshots"
    database_url: str = "sqlite:///./anpr.db"
    relay_mode: str = "mock"
    relay_pin: int = 17

    class Config:
        env_file = ".env"

settings = Settings()
