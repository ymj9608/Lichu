from pathlib import Path
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=Path(__file__).resolve().parents[3] / '.env', extra='ignore')
    database_url: str = 'postgresql+psycopg://lichu:lichu_local@localhost:55434/lichu'
    jwt_secret: str = Field(min_length=32)
    access_token_minutes: int = Field(default=120, ge=1)
    cors_origins: str = 'http://localhost:5173,http://127.0.0.1:5173'
    master_password: str = ''
    demo_password: str = ''
    csi_lab_mode: bool = False


settings = Settings()
