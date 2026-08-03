## backend/app/config.py
import os
from pydantic import Field
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
    cors_origins: list = [
        "http://localhost:5173",
        "http://localhost:3000",
        "http://127.0.0.1:5173",
        "http://54.233.94.150:5173",
    ]
    cors_credentials: bool = True
    cors_methods: list = ["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"]
    cors_headers: list = ["Authorization", "Content-Type", "Accept", "Origin", "X-Requested-With"]
    
    # Traccar – lido do .env via Field
    traccar_url: str = Field(default="http://localhost:8082", env="TRACCAR_URL")
    traccar_admin_user: str = Field(default="admin", env="TRACCAR_ADMIN_USER")
    traccar_admin_password: str = Field(default="admin", env="TRACCAR_ADMIN_PASSWORD")

    # Route matching provider settings
    route_matching_provider: str = Field(default="openrouteservice", env="ROUTE_MATCHING_PROVIDER")
    ors_url: str = Field(default="https://api.openrouteservice.org", env="ORS_URL")
    ors_api_key: Optional[str] = Field(default=None, env="ORS_API_KEY")
    ors_profile: str = Field(default="driving-car", env="ORS_PROFILE")
    route_matching_cache_size: int = Field(default=128, env="ROUTE_MATCHING_CACHE_SIZE")

    # Redis
    redis_url: Optional[str] = "redis://localhost:6379"
    
    # Tracking
    gps_update_interval_moving: int = 30
    gps_update_interval_stationary: int = 120
    battery_alert_threshold: int = 15
    
    # Data Retention
    # Quantos dias de histórico manter antes da limpeza automática apagar os registros.
    # Configuráveis via variáveis de ambiente POSITION_RETENTION_DAYS / EVENT_RETENTION_DAYS.
    position_retention_days: int = Field(default=90, env="POSITION_RETENTION_DAYS")
    event_retention_days: int = Field(default=180, env="EVENT_RETENTION_DAYS")

    # A cada quantas horas o job de limpeza roda (padrão: 24h = uma vez por dia)
    retention_cleanup_interval_hours: int = Field(default=24, env="RETENTION_CLEANUP_INTERVAL_HOURS")
    # Quantos registros são apagados por lote, para não travar o banco com um DELETE gigante
    retention_cleanup_batch_size: int = Field(default=500, env="RETENTION_CLEANUP_BATCH_SIZE")
    # Permite desligar a limpeza automática sem remover o código (ex: ambientes de teste)
    retention_cleanup_enabled: bool = Field(default=True, env="RETENTION_CLEANUP_ENABLED")
    
    class Config:
        env_file = ".env"
        case_sensitive = False


@lru_cache()
def get_settings() -> Settings:
    return Settings()