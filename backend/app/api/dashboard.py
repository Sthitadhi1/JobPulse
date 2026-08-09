import datetime
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func

from backend.app.database import get_db
from backend.app.models.application import JobApplication
from backend.app.models.job import Job

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])

@router.get("/metrics")
async def get_dashboard_metrics(db: AsyncSession = Depends(get_db)):
    """
    PART 12 — Dashboard Analytics Cards
    Applications, Interviews, Offers, Rejections, Response Rate %, Weekly Volume.
    """
    # Total Applications in workspace
    total_apps_res = await db.execute(select(func.count(JobApplication.id)))
    total_apps = total_apps_res.scalar() or 0

    # Active Interviews (Interview, HR Round, OA Scheduled)
    interviews_res = await db.execute(
        select(func.count(JobApplication.id)).where(JobApplication.status.in_(["OA Scheduled", "Interview", "HR Round"]))
    )
    interviews_count = interviews_res.scalar() or 0

    # Offers Count
    offers_res = await db.execute(
        select(func.count(JobApplication.id)).where(JobApplication.status == "Offer")
    )
    offers_count = offers_res.scalar() or 0

    # Rejections Count
    rejections_res = await db.execute(
        select(func.count(JobApplication.id)).where(JobApplication.status == "Rejected")
    )
    rejections_count = rejections_res.scalar() or 0

    # Response Rate % = (Interviews + Offers + Rejections) / Total Applied
    applied_count_res = await db.execute(
        select(func.count(JobApplication.id)).where(JobApplication.status != "Saved")
    )
    applied_count = applied_count_res.scalar() or 1
    responses_count = interviews_count + offers_count + rejections_count
    response_rate = round((responses_count / applied_count) * 100.0, 1) if applied_count > 0 else 0.0

    # Applications This Week
    one_week_ago = datetime.datetime.utcnow() - datetime.timedelta(days=7)
    weekly_res = await db.execute(
        select(func.count(JobApplication.id)).where(JobApplication.created_at >= one_week_ago)
    )
    weekly_count = weekly_res.scalar() or 0

    # Total Discovered Jobs in System
    total_jobs_res = await db.execute(select(func.count(Job.id)).where(Job.status == "ACTIVE"))
    total_jobs = total_jobs_res.scalar() or 0

    return {
        "success": True,
        "metrics": {
            "total_applications": total_apps,
            "active_interviews": interviews_count,
            "offers_received": offers_count,
            "rejections": rejections_count,
            "response_rate_pct": response_rate,
            "applications_this_week": weekly_count,
            "total_discovered_jobs": total_jobs
        }
    }
