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
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./jobpulse.db")
    SYNC_INTERVAL_MINUTES: int = 15
    TELEGRAM_BOT_TOKEN: str = os.getenv("TELEGRAM_BOT_TOKEN", "MOCK_TELEGRAM_BOT_TOKEN")
    ENABLE_SCHEDULER: bool = os.getenv("ENABLE_SCHEDULER", "True").lower() in ("true", "1", "yes")

    # Production & Security Configuration
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")
    SECURE_COOKIES: bool = os.getenv("SECURE_COOKIES", "False").lower() in ("true", "1", "yes")
    SECRET_KEY: str = os.getenv("SECRET_KEY", "jobpulse-secret-key-change-in-production-32bytes!")
    SESSION_SECRET: str = os.getenv("SESSION_SECRET", "jobpulse-session-secret-change-in-production!")
    SCHEDULER_SECRET: str = os.getenv("SCHEDULER_SECRET", "jobpulse-internal-scheduler-secret")
    CONNECTOR_MAX_CONCURRENCY: int = int(os.getenv("CONNECTOR_MAX_CONCURRENCY", "5"))
    DISCOVERY_INTERVAL_SECONDS: int = int(os.getenv("DISCOVERY_INTERVAL_SECONDS", "60" if os.getenv("ENVIRONMENT", "development") == "development" else "3600"))
    DISCOVERY_LOCK_TIMEOUT_SECONDS: int = int(os.getenv("DISCOVERY_LOCK_TIMEOUT_SECONDS", "900" if os.getenv("ENVIRONMENT", "development") == "development" else "3600"))
    JOB_MISSING_CYCLES_THRESHOLD: int = int(os.getenv("JOB_MISSING_CYCLES_THRESHOLD", "2" if os.getenv("ENVIRONMENT", "development") == "development" else "3"))
    ALLOWED_ORIGINS: str = os.getenv("ALLOWED_ORIGINS", "http://localhost:8000,http://127.0.0.1:8000,http://localhost:3000")


    # SMTP & Email Settings
    SMTP_HOST: str = os.getenv("SMTP_HOST", "")
    SMTP_PORT: int = int(os.getenv("SMTP_PORT", "587"))
    SMTP_USERNAME: str = os.getenv("SMTP_USERNAME", "")
    SMTP_PASSWORD: str = os.getenv("SMTP_PASSWORD", "")
    EMAIL_FROM: str = os.getenv("EMAIL_FROM", "noreply@jobpulse.io")
    EMAIL_FROM_NAME: str = os.getenv("EMAIL_FROM_NAME", "JobPulse Alerts")
    
    # Auth & Security Timers
    OTP_EXPIRY_MINUTES: int = int(os.getenv("OTP_EXPIRY_MINUTES", "10"))
    VERIFICATION_TOKEN_EXPIRY_HOURS: int = int(os.getenv("VERIFICATION_TOKEN_EXPIRY_HOURS", "24"))

    class Config:
        env_file = ".env"
        extra = "ignore"

settings = Settings()

