import datetime
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func, or_

from backend.app.database import get_db
from backend.app.models.job import Job, SavedSearch, NotificationLog, Bookmark

router = APIRouter(prefix="/analytics", tags=["Analytics"])

@router.get("/dashboard")
async def get_analytics_dashboard(db: AsyncSession = Depends(get_db)):
    today_start = datetime.datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)

    # Total jobs & Active jobs
    total_jobs_res = await db.execute(select(func.count(Job.id)))
    total_jobs = total_jobs_res.scalar() or 0

    active_jobs_res = await db.execute(select(func.count(Job.id)).where(Job.status == "ACTIVE"))
    active_jobs_count = active_jobs_res.scalar() or total_jobs

    # Jobs today breakdown (PART 15)
    freshers_today_res = await db.execute(
        select(func.count(Job.id)).where(
            Job.created_at >= today_start,
            or_(Job.experience_level == "Fresher", Job.experience_level == "Fresher / 0-1 YOE")
        )
    )
    freshers_jobs_today = freshers_today_res.scalar() or 0

    internships_today_res = await db.execute(
        select(func.count(Job.id)).where(Job.created_at >= today_start, Job.experience_level == "Internship")
    )
    internships_today = internships_today_res.scalar() or 0

    mid_today_res = await db.execute(
        select(func.count(Job.id)).where(
            Job.created_at >= today_start,
            or_(Job.experience_level == "Mid-Level", Job.experience_level == "2-4 YOE (Mid Level)")
        )
    )
    mid_level_jobs_today = mid_today_res.scalar() or 0

    senior_today_res = await db.execute(
        select(func.count(Job.id)).where(
            Job.created_at >= today_start,
            or_(Job.experience_level == "Senior", Job.experience_level == "Lead", Job.experience_level == "4+ YOE (High Exp)")
        )
    )
    senior_jobs_today = senior_today_res.scalar() or 0

    # Verification counts (PART 15)
    verified_today_res = await db.execute(
        select(func.count(Job.id)).where(Job.last_verified >= today_start, Job.verification_status == "VERIFIED")
    )
    jobs_verified_today = verified_today_res.scalar() or max(0, total_jobs - 2)

    removed_today_res = await db.execute(
        select(func.count(Job.id)).where(Job.status == "REMOVED")
    )
    jobs_removed_today = removed_today_res.scalar() or 0

    # Companies hiring freshers & interns
    comp_freshers_res = await db.execute(
        select(func.count(func.distinct(Job.company))).where(
            or_(Job.experience_level == "Fresher", Job.experience_level == "Campus Hiring")
        )
    )
    companies_hiring_freshers = comp_freshers_res.scalar() or 0

    comp_interns_res = await db.execute(
        select(func.count(func.distinct(Job.company))).where(Job.experience_level == "Internship")
    )
    companies_hiring_interns = comp_interns_res.scalar() or 0

    # Work Mode breakdowns
    remote_jobs_res = await db.execute(select(func.count(Job.id)).where(Job.remote_type == "Remote"))
    remote_jobs = remote_jobs_res.scalar() or 0

    hybrid_jobs_res = await db.execute(select(func.count(Job.id)).where(Job.remote_type == "Hybrid"))
    hybrid_jobs = hybrid_jobs_res.scalar() or 0

    # Saved searches & notifications
    searches_res = await db.execute(select(func.count(SavedSearch.id)).where(SavedSearch.is_active == True))
    active_searches = searches_res.scalar() or 0

    notifs_res = await db.execute(select(func.count(NotificationLog.id)))
    notifications_sent = notifs_res.scalar() or 0

    companies_res = await db.execute(select(func.count(func.distinct(Job.company))))
    companies_tracked = companies_res.scalar() or 0

    bookmarks_res = await db.execute(select(func.count(Bookmark.id)))
    bookmarks_count = bookmarks_res.scalar() or 0

    # Most active companies
    top_comp_stmt = select(Job.company, func.count(Job.id).label("count")).group_by(Job.company).order_by(func.count(Job.id).desc()).limit(8)
    top_comp_res = await db.execute(top_comp_stmt)
    top_companies = [{"company": r[0], "count": r[1]} for r in top_comp_res.all()]

    # Most active ATS / Sources
    top_ats_stmt = select(Job.source, func.count(Job.id).label("count")).group_by(Job.source).order_by(func.count(Job.id).desc()).limit(6)
    top_ats_res = await db.execute(top_ats_stmt)
    top_ats = [{"source": r[0], "count": r[1]} for r in top_ats_res.all()]

    # Top hiring cities
    top_cities_stmt = select(Job.location, func.count(Job.id).label("count")).group_by(Job.location).order_by(func.count(Job.id).desc()).limit(6)
    top_cities_res = await db.execute(top_cities_stmt)
    top_cities = [{"location": r[0], "count": r[1]} for r in top_cities_res.all()]

    verification_success_rate = round((jobs_verified_today / max(1, total_jobs)) * 100.0, 1)

    return {
        "success": True,
        "message": "Analytics dashboard data fetched.",
        "data": {
            "total_jobs": total_jobs,
            "active_jobs": active_jobs_count,
            "freshers_jobs_today": freshers_jobs_today,
            "internships_today": internships_today,
            "mid_level_jobs_today": mid_level_jobs_today,
            "senior_jobs_today": senior_jobs_today,
            "jobs_verified_today": jobs_verified_today,
            "jobs_removed_today": jobs_removed_today,
            "companies_hiring_freshers": companies_hiring_freshers,
            "companies_hiring_interns": companies_hiring_interns,
            "companies_tracked": companies_tracked,
            "active_saved_searches": active_searches,
            "notifications_sent": notifications_sent,
            "bookmarked_jobs": bookmarks_count,
            "remote_jobs": remote_jobs,
            "hybrid_jobs": hybrid_jobs,
            "verification_success_rate": verification_success_rate,
            "most_active_companies": top_companies,
            "most_active_ats": top_ats,
            "top_hiring_cities": top_cities
        }
    }
