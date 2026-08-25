import datetime
import json
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func

from backend.app.database import get_db
from backend.app.models.application import JobApplication
from backend.app.models.job import Job, Bookmark, CandidateProfile, User
from backend.app.api.auth import get_current_user_optional
from backend.app.engine.ai_layer import AIEngineLayer

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])

@router.get("/metrics")
async def get_dashboard_metrics(db: AsyncSession = Depends(get_db)):
    """Analytics cards & metrics."""
    total_apps_res = await db.execute(select(func.count(JobApplication.id)))
    total_apps = total_apps_res.scalar() or 0

    interviews_res = await db.execute(
        select(func.count(JobApplication.id)).where(JobApplication.status.in_(["OA Scheduled", "Interview", "HR Round"]))
    )
    interviews_count = interviews_res.scalar() or 0

    offers_res = await db.execute(
        select(func.count(JobApplication.id)).where(JobApplication.status == "Offer")
    )
    offers_count = offers_res.scalar() or 0

    rejections_res = await db.execute(
        select(func.count(JobApplication.id)).where(JobApplication.status == "Rejected")
    )
    rejections_count = rejections_res.scalar() or 0

    applied_count_res = await db.execute(
        select(func.count(JobApplication.id)).where(JobApplication.status != "Saved")
    )
    applied_count = applied_count_res.scalar() or 1
    responses_count = interviews_count + offers_count + rejections_count
    response_rate = round((responses_count / max(1, applied_count)) * 100.0, 1)

    one_week_ago = datetime.datetime.utcnow() - datetime.timedelta(days=7)
    weekly_res = await db.execute(
        select(func.count(JobApplication.id)).where(JobApplication.created_at >= one_week_ago)
    )
    weekly_count = weekly_res.scalar() or 0

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


@router.get("/overview")
async def get_dashboard_overview(
    current_user: Depends = Depends(get_current_user_optional),
    db: AsyncSession = Depends(get_db)
):
    """
    Command-Center Dashboard Overview Endpoint.
    Returns:
    - User Greeting Name
    - Overview Stat Cards (Active Jobs, Top Matches, Applications, Bookmarked)
    - Top Matches Preview list (Top 3-4 recommended jobs)
    - Recent Applications Pipeline breakdown (Saved, Applied, OA/Test, Interview, Offer)
    """
    user_name = current_user.name if current_user else "Sthitadhi"

    # 1. Active Jobs Count (Live & Verified ACTIVE)
    active_jobs_res = await db.execute(select(func.count(Job.id)).where(Job.status == "ACTIVE"))
    active_jobs_count = active_jobs_res.scalar() or 0

    # 2. Bookmarked Jobs Count
    if current_user:
        bm_res = await db.execute(select(func.count(Bookmark.id)).where(Bookmark.user_id == current_user.id))
    else:
        bm_res = await db.execute(select(func.count(Job.id)).where(Job.is_bookmarked == True))
    bookmarked_count = bm_res.scalar() or 0

    # 3. Applications Count & Pipeline Breakdown
    saved_res = await db.execute(select(func.count(JobApplication.id)).where(JobApplication.status == "Saved"))
    saved_count = saved_res.scalar() or 0

    applied_res = await db.execute(select(func.count(JobApplication.id)).where(JobApplication.status == "Applied"))
    applied_count = applied_res.scalar() or 0

    oa_res = await db.execute(select(func.count(JobApplication.id)).where(JobApplication.status.in_(["OA Scheduled", "OA / Test", "Interview"])))
    oa_count = oa_res.scalar() or 0

    interview_res = await db.execute(select(func.count(JobApplication.id)).where(JobApplication.status.in_(["Interview", "HR Round"])))
    interview_count = interview_res.scalar() or 0

    offer_res = await db.execute(select(func.count(JobApplication.id)).where(JobApplication.status == "Offer"))
    offer_count = offer_res.scalar() or 0

    total_applications = saved_count + applied_count + oa_count + interview_count + offer_count

    # 4. Top Matches Preview
    cand_profile = None
    if current_user:
        cp_res = await db.execute(select(CandidateProfile).where(CandidateProfile.user_id == current_user.id))
        cp = cp_res.scalars().first()
        if cp and cp.parsed_json:
            try:
                cand_profile = json.loads(cp.parsed_json)
            except Exception:
                cand_profile = None

    if not cand_profile:
        cand_profile = {
            "name": user_name,
            "experience_level": "Fresher",
            "skills": ["Python", "Java", "React", "FastAPI", "SQL", "Data Structures"],
            "preferred_roles": ["Software Development Engineer (SDE 1)", "Backend Engineer"]
        }

    top_recs = await AIEngineLayer.get_top_30_recommendations(db, cand_profile)
    top_matches_count = len(top_recs)
    top_matches_preview = top_recs[:3] # Top 3 preview items

    return {
        "success": True,
        "user_name": user_name,
        "overview": {
            "active_jobs": active_jobs_count,
            "top_matches": top_matches_count,
            "applications": total_applications,
            "bookmarked_jobs": bookmarked_count
        },
        "top_matches_preview": top_matches_preview,
        "pipeline": {
            "saved": saved_count,
            "applied": applied_count,
            "oa_test": oa_count,
            "interview": interview_count,
            "offer": offer_count
        }
    }
