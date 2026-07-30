import os
try:
    from pydantic_settings import BaseSettings
except ImportError:
    try:
        from pydantic import BaseSettings
    except ImportError:
        from pydantic.v1 import BaseSettings

class Settings(BaseSettings):
    PROJECT_NAME: str = "JobPulse"
    VERSION: str = "1.0.0"
    API_PREFIX: str = "/api/v1"
    DATABASE_URL: str = "sqlite+aiosqlite:///./jobpulse.db"
    SYNC_INTERVAL_MINUTES: int = 15
    TELEGRAM_BOT_TOKEN: str = os.getenv("TELEGRAM_BOT_TOKEN", "MOCK_TELEGRAM_BOT_TOKEN")
    ENABLE_SCHEDULER: bool = True

    class Config:
        env_file = ".env"
        extra = "ignore"

settings = Settings()
