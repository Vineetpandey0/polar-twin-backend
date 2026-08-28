from typing import List
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql+asyncpg://polartwin_user:polartwin_pass@localhost:5432/polartwin_db"
    MQTT_HOST: str = "localhost"
    MQTT_PORT: int = 1883
    ANTHROPIC_API_KEY: str = "dummy_key"
    BACKEND_PORT: int = 8000
    # Comma-separated list of allowed CORS origins, e.g.:
    # CORS_ORIGINS=https://your-app.vercel.app,http://localhost:3000
    CORS_ORIGINS: str = "http://localhost:3000"

    @property
    def cors_origins_list(self) -> List[str]:
        return [o.strip() for o in self.CORS_ORIGINS.split(",") if o.strip()]

    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )


settings = Settings()
