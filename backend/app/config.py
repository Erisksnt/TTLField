from pydantic_settings import BaseSettings
from typing import Optional
from functools import lru_cache


class Settings(BaseSettings):
    # App
    app_name: str = "ISP Tracker Platform"
    app_version: str = "1.0.0"
    environment: str = "development"
    debug: bool = True

    # Database
    database_url: str = "postgresql://tracker_user:secure_password@localhost:5432/isp_tracker"
    
    # Security
    secret_key: str = "your-secret-key-change-in-production"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 7
    
    # JWT
    jwt_expiration_hours: int = 24
    
    # CORS
    cors_origins: list = ["*"]
    cors_credentials: bool = True
    cors_methods: list = ["*"]
    cors_headers: list = ["*"]
    
    # Traccar
    traccar_url: str = "http://localhost:8082"
    traccar_admin_user: str = "admin"
    traccar_admin_password: str = "admin"
    
    # Redis
    redis_url: Optional[str] = "redis://localhost:6379"
    
    # Tracking
    gps_update_interval_moving: int = 30  # seconds
    gps_update_interval_stationary: int = 120  # seconds
    battery_alert_threshold: int = 15  # percent
    
    # Data Retention
    position_retention_days: int = 90
    event_retention_days: int = 365
    
    class Config:
        env_file = ".env"
        case_sensitive = False


@lru_cache()
def get_settings() -> Settings:
    return Settings()