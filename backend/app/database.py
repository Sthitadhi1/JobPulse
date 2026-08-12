from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy import text, event
from backend.app.config import settings

engine_kwargs = {
    "echo": False,
    "future": True
}
if "sqlite" in settings.DATABASE_URL:
    engine_kwargs["connect_args"] = {"timeout": 30.0}

engine = create_async_engine(
    settings.DATABASE_URL,
    **engine_kwargs
)

if "sqlite" in settings.DATABASE_URL:
    @event.listens_for(engine.sync_engine, "connect")
    def set_sqlite_pragma(dbapi_connection, connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA journal_mode=WAL")
        cursor.execute("PRAGMA busy_timeout=30000")
        cursor.execute("PRAGMA synchronous=NORMAL")
        cursor.close()

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
    # Import all models to ensure they are registered with Base.metadata
    import backend.app.models

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        
        # Safely query existing columns per table to avoid SQLite transaction aborts
        async def get_existing_columns(table_name: str) -> set:
            try:
                res = await conn.execute(text(f"PRAGMA table_info({table_name})"))
                return {row[1] for row in res.fetchall()}
            except Exception:
                return set()

        job_cols = await get_existing_columns("jobs")
        job_migrations = [
            ("job_url", "ALTER TABLE jobs ADD COLUMN job_url TEXT DEFAULT '#'"),
            ("source_url", "ALTER TABLE jobs ADD COLUMN source_url TEXT DEFAULT '#'"),
            ("external_apply_url", "ALTER TABLE jobs ADD COLUMN external_apply_url TEXT NULL"),
            ("discovered_at", "ALTER TABLE jobs ADD COLUMN discovered_at DATETIME NULL"),
            ("department", "ALTER TABLE jobs ADD COLUMN department VARCHAR(150) NULL"),
            ("country", "ALTER TABLE jobs ADD COLUMN country VARCHAR(100) DEFAULT 'India'"),
            ("skills", "ALTER TABLE jobs ADD COLUMN skills TEXT NULL"),
            ("benefits", "ALTER TABLE jobs ADD COLUMN benefits TEXT NULL"),
            ("status", "ALTER TABLE jobs ADD COLUMN status VARCHAR(50) DEFAULT 'ACTIVE'"),
            ("verification_status", "ALTER TABLE jobs ADD COLUMN verification_status VARCHAR(50) DEFAULT 'VERIFIED'"),
            ("first_seen", "ALTER TABLE jobs ADD COLUMN first_seen DATETIME NULL"),
            ("last_seen", "ALTER TABLE jobs ADD COLUMN last_seen DATETIME NULL"),
            ("last_verified", "ALTER TABLE jobs ADD COLUMN last_verified DATETIME NULL"),
            ("verification_count", "ALTER TABLE jobs ADD COLUMN verification_count INTEGER DEFAULT 1"),
            ("consecutive_missing_count", "ALTER TABLE jobs ADD COLUMN consecutive_missing_count INTEGER DEFAULT 0")
        ]

        for col_name, stmt in job_migrations:
            if col_name not in job_cols:
                try:
                    await conn.execute(text(stmt))
                except Exception:
                    pass

        user_cols = await get_existing_columns("users")
        user_migrations = [
            ("telegram_connected", "ALTER TABLE users ADD COLUMN telegram_connected BOOLEAN DEFAULT 0"),
            ("telegram_token", "ALTER TABLE users ADD COLUMN telegram_token VARCHAR(100) NULL"),
            ("last_notification_sent", "ALTER TABLE users ADD COLUMN last_notification_sent DATETIME NULL"),
            ("email_verified", "ALTER TABLE users ADD COLUMN email_verified BOOLEAN DEFAULT 0"),
            ("last_login_at", "ALTER TABLE users ADD COLUMN last_login_at DATETIME NULL"),
            ("updated_at", "ALTER TABLE users ADD COLUMN updated_at DATETIME NULL")
        ]
        for col_name, stmt in user_migrations:
            if col_name not in user_cols:
                try:
                    await conn.execute(text(stmt))
                except Exception:
                    pass

        health_cols = await get_existing_columns("connector_health")
        health_migrations = [
            ("jobs_verified", "ALTER TABLE connector_health ADD COLUMN jobs_verified INTEGER DEFAULT 0"),
            ("jobs_removed", "ALTER TABLE connector_health ADD COLUMN jobs_removed INTEGER DEFAULT 0")
        ]
        for col_name, stmt in health_migrations:
            if col_name not in health_cols:
                try:
                    await conn.execute(text(stmt))
                except Exception:
                    pass

        exec_cols = await get_existing_columns("connector_executions")
        exec_migrations = [
            ("jobs_verified", "ALTER TABLE connector_executions ADD COLUMN jobs_verified INTEGER DEFAULT 0"),
            ("jobs_removed", "ALTER TABLE connector_executions ADD COLUMN jobs_removed INTEGER DEFAULT 0"),
            ("execution_id", "ALTER TABLE connector_executions ADD COLUMN execution_id VARCHAR(36) NULL")
        ]
        for col_name, stmt in exec_migrations:
            if col_name not in exec_cols:
                try:
                    await conn.execute(text(stmt))
                except Exception:
                    pass



