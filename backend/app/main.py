import os
import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sqlalchemy.future import select

from backend.app.config import settings
from backend.app.database import init_db, AsyncSessionLocal
from backend.app.models.job import Job
from backend.app.engine.verification import VerificationEngine
from backend.app.engine.scheduler import scheduler_engine
from backend.app.api.jobs import router as jobs_router
from backend.app.api.searches import router as searches_router
from backend.app.api.connectors import router as connectors_router
from backend.app.api.notifications import router as notifications_router
from backend.app.api.analytics import router as analytics_router
from backend.app.api.ai import router as ai_router
from backend.app.api.applications import router as applications_router
from backend.app.api.dashboard import router as dashboard_router

async def run_startup_seed():
    await asyncio.sleep(1.0)
    async with AsyncSessionLocal() as session:
        try:
            await scheduler_engine.run_discovery_cycle(session)
        except Exception as e:
            print(f"[STARTUP SEED ERROR] {e}")

async def run_15min_dead_link_worker():
    """
    Continuous Background Worker (runs every 15 minutes / 900 seconds):
    Verifies all ACTIVE jobs in the database with concurrent HEAD/GET requests.
    Automatically marks 404 / 410 / dead listings as REMOVED.
    """
    while True:
        try:
            await asyncio.sleep(900) # 15 minutes
            print("[15-MIN WORKER] Starting continuous dead link verification cycle...")
            async with AsyncSessionLocal() as session:
                res = await session.execute(select(Job).where(Job.status == "ACTIVE"))
                active_jobs = res.scalars().all()
                v_count, r_count = await VerificationEngine.verify_jobs_batch(session, active_jobs)
                print(f"[15-MIN WORKER] Verification complete. Verified live: {v_count}, Auto-removed dead 404s: {r_count}")
        except Exception as e:
            print(f"[15-MIN WORKER ERROR] {e}")

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize DB tables
    await init_db()
    
    # Launch startup seed and 15-minute continuous dead-link worker
    asyncio.create_task(run_startup_seed())
    asyncio.create_task(run_15min_dead_link_worker())

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
app.include_router(applications_router, prefix=prefix)
app.include_router(dashboard_router, prefix=prefix)

# Mount static frontend dashboard
frontend_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "frontend")
if os.path.exists(frontend_dir):
    app.mount("/dashboard", StaticFiles(directory=frontend_dir, html=True), name="frontend")

@app.get("/")
async def root():
    return {
        "project": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "status": "ONLINE",
        "documentation": "/docs"
    }
