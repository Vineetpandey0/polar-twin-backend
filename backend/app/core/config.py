from typing import List
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql+asyncpg://polartwin_user:polartwin_pass@localhost:5432/polartwin_db"
    MQTT_HOST: str = "polar-twin-backend.up.railway.app" or "localhost"
    MQTT_PORT: int = 1883
    ANTHROPIC_API_KEY: str = "dummy_key"
    BACKEND_PORT: int = 8000
    # Comma-separated list of allowed CORS origins (* or specific domains)
    CORS_ORIGINS: str = "*"
    SIMULATION_INTERVAL_SECONDS: float = 600.0  # 10 minutes cadence

    @property
    def cors_origins_list(self) -> List[str]:
        if self.CORS_ORIGINS == "*":
            return ["*"]
        return [o.strip().rstrip("/") for o in self.CORS_ORIGINS.split(",") if o.strip()]

    model_config = SettingsConfigDict(
        env_file=(".env", "../.env"), env_file_encoding="utf-8", extra="ignore"
    )


settings = Settings()
