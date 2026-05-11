from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    app_name: str = "ISP Tracker"
    app_version: str = "1.0.0"
    database_url: str = "postgresql://tracker_user:secure_password@postgres:5432/isp_tracker"
    secret_key: str = "your-secret-key"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    
    class Config:
        env_file = ".env"

settings = Settings()