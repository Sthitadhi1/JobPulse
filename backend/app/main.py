from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from backend.app.config import settings
from backend.app.database import init_db, AsyncSessionLocal
from backend.app.api.jobs import router as jobs_router
from backend.app.api.searches import router as searches_router
from backend.app.api.connectors import router as connectors_router
from backend.app.api.notifications import router as notifications_router
from backend.app.api.analytics import router as analytics_router
from backend.app.api.ai import router as ai_router
from backend.app.engine.scheduler import scheduler_engine

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize DB tables
    await init_db()
    
    # Run seed discovery cycle on startup
    async with AsyncSessionLocal() as session:
        try:
            await scheduler_engine.run_discovery_cycle(session)
        except Exception as e:
            print(f"[STARTUP SEED ERROR] {e}")

    yield

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="Open-source real-time job discovery engine for students & early career engineers.",
    lifespan=lifespan
)

# Enable CORS for local dev
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount REST API Routers under /api/v1
prefix = settings.API_PREFIX
app.include_router(jobs_router, prefix=prefix)
app.include_router(searches_router, prefix=prefix)
app.include_router(connectors_router, prefix=prefix)
app.include_router(notifications_router, prefix=prefix)
app.include_router(analytics_router, prefix=prefix)
app.include_router(ai_router, prefix=prefix)

@app.get("/")
async def root():
    return {
        "project": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "status": "ONLINE",
        "documentation": "/docs"
    }
