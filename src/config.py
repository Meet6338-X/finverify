"""
Application configuration management using Pydantic Settings.
"""
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import computed_field

class Settings(BaseSettings):
    postgres_user: str = "finverify"
    postgres_password: str = "changeme"
    postgres_db: str = "finverify"
    postgres_host: str = "postgres"
    postgres_port: int = 5432
    
    redis_host: str = "redis"
    redis_port: int = 6379
    
    temporal_host: str = "temporal"
    temporal_port: int = 7233
    temporal_namespace: str = "default"
    temporal_task_queue: str = "finverify-task-queue"
    
    sec_edgar_user_agent: str = "FinVerify/1.0 (contact@finverify.io)"
    
    finverify_signing_key_path: str = "/app/keys/signing_key.pem"
    finverify_public_key_path: str = "/app/keys/public_key.pem"
    
    jwt_secret: str = "changeme-jwt-secret"
    jwt_algorithm: str = "HS256"
    
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    
    frontend_url: str = "http://localhost:3000"
    
    log_level: str = "INFO"

    @computed_field
    @property
    def database_url(self) -> str:
        return f"postgresql+asyncpg://{self.postgres_user}:{self.postgres_password}@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

settings = Settings()
