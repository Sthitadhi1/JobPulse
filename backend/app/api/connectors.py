from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from backend.app.database import get_db
from backend.app.models.job import ConnectorHealth
from backend.app.engine.scheduler import scheduler_engine

router = APIRouter(prefix="/admin/connectors", tags=["Admin Connectors"])

@router.get("")
async def get_connector_health(db: AsyncSession = Depends(get_db)):
    res = await db.execute(select(ConnectorHealth).order_by(ConnectorHealth.id.asc()))
    records = res.scalars().all()

    return {
        "success": True,
        "message": "Connector health status fetched.",
        "data": [
            {
                "id": r.id,
                "name": r.name,
                "source_type": r.source_type,
                "status": r.status,
                "last_run": r.last_run.isoformat() if r.last_run else None,
                "jobs_found_last_run": r.jobs_found_last_run,
                "total_jobs_indexed": r.total_jobs_indexed,
                "average_runtime_ms": r.average_runtime_ms,
                "error_message": r.error_message
            }
            for r in records
        ]
    }

@router.post("/sync")
async def trigger_manual_sync(db: AsyncSession = Depends(get_db)):
    result = await scheduler_engine.run_discovery_cycle(db)
    return {
        "success": True,
        "message": "Manual connector discovery cycle completed.",
        "data": result
    }
