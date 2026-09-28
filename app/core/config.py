import os
from typing import List, Optional
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    PROJECT_NAME: str = "RS Juris & Co. Legal API"
    API_V1_STR: str = "/api/v1"
    SECRET_KEY: str = "default_secret_key_change_in_production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 480

    # Make DATABASE_URL provide a fallback or accept direct entry
    DATABASE_URL: Optional[str] = None

    # Fallbacks if individual keys exist
    POSTGRES_SERVER: Optional[str] = "localhost"
    POSTGRES_USER: Optional[str] = "postgres"
    POSTGRES_PASSWORD: Optional[str] = "postgres"
    POSTGRES_DB: Optional[str] = "rsjuris_db"
    POSTGRES_PORT: Optional[int] = 5432

    CLOUDINARY_CLOUD_NAME: str = ""
    CLOUDINARY_API_KEY: str = ""
    CLOUDINARY_API_SECRET: str = ""

    BACKEND_CORS_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://127.0.0.1:3000"
    ]

    def _get_base_url(self) -> str:
        if self.DATABASE_URL:
            return self.DATABASE_URL
        return f"postgresql://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_SERVER}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"

    @property
    def async_database_url(self) -> str:
        url = self._get_base_url()
        # Ensure asyncpg driver protocol
        if url.startswith("postgres://"):
            url = url.replace("postgres://", "postgresql+asyncpg://", 1)
        elif url.startswith("postgresql://"):
            url = url.replace("postgresql://", "postgresql+asyncpg://", 1)

        # 1. asyncpg does not support channel_binding
        url = url.replace("&channel_binding=require", "").replace("?channel_binding=require&", "?").replace("?channel_binding=require", "")
        
        # 2. Convert sslmode=... to ssl=... for asyncpg
        url = url.replace("sslmode=require", "ssl=require").replace("sslmode=verify-full", "ssl=require").replace("sslmode=prefer", "ssl=require")

        # 3. Ensure ssl parameter is present
        if "ssl=" not in url:
            connector = "&" if "?" in url else "?"
            url = f"{url}{connector}ssl=require"

        return url

    @property
    def sync_database_url(self) -> str:
        url = self._get_base_url()
        # Alembic / psycopg2 driver protocol
        if url.startswith("postgres://"):
            url = url.replace("postgres://", "postgresql+psycopg2://", 1)
        elif url.startswith("postgresql://"):
            url = url.replace("postgresql://", "postgresql+psycopg2://", 1)

        url = url.replace("&channel_binding=require", "").replace("?channel_binding=require&", "?").replace("?channel_binding=require", "")
        
        # Ensure sslmode=require exists for psycopg2
        if "sslmode=" not in url:
            connector = "&" if "?" in url else "?"
            url = f"{url}{connector}sslmode=require"

        return url

    class Config:
        env_file = ".env"
        extra = "ignore"

settings = Settings()