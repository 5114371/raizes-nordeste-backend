"""Configuracoes centrais da aplicacao."""
import os
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    app_name: str = "Raizes do Nordeste API"
    database_url: str = os.getenv("DATABASE_URL", "postgresql://raizes:raizes123@localhost:5432/raizes_db")
    redis_url: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    jwt_secret: str = os.getenv("JWT_SECRET", "mude-essa-chave")
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 60
    bcrypt_cost: int = 12
    gateway_secret: str = os.getenv("GATEWAY_WEBHOOK_SECRET", "mock-secret-123")

    class Config:
        env_file = ".env"


settings = Settings()
