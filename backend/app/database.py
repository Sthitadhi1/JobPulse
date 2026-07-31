from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy import text
from backend.app.config import settings

engine = create_async_engine(
    settings.DATABASE_URL,
    echo=False,
    future=True
)

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False
)

class Base(DeclarativeBase):
    pass

async def get_db():
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()

async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        
        # Automatic SQLite column migrations for backward compatibility
        try:
            await conn.execute(text("ALTER TABLE jobs ADD COLUMN job_url TEXT DEFAULT '#'"))
        except Exception:
            pass
        try:
            await conn.execute(text("ALTER TABLE jobs ADD COLUMN source_url TEXT DEFAULT '#'"))
        except Exception:
            pass
        try:
            await conn.execute(text("ALTER TABLE jobs ADD COLUMN external_apply_url TEXT NULL"))
        except Exception:
            pass
        try:
            await conn.execute(text("ALTER TABLE jobs ADD COLUMN discovered_at DATETIME DEFAULT CURRENT_TIMESTAMP"))
        except Exception:
            pass
        try:
            await conn.execute(text("ALTER TABLE users ADD COLUMN telegram_connected BOOLEAN DEFAULT 0"))
        except Exception:
            pass
        try:
            await conn.execute(text("ALTER TABLE users ADD COLUMN telegram_token VARCHAR(100) NULL"))
        except Exception:
            pass
        try:
            await conn.execute(text("ALTER TABLE users ADD COLUMN last_notification_sent DATETIME NULL"))
        except Exception:
            pass
