import datetime
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func

from backend.app.database import get_db
from backend.app.models.job import Job, SavedSearch, NotificationLog, ConnectorHealth, Bookmark

router = APIRouter(prefix="/analytics", tags=["Analytics"])

@router.get("/dashboard")
async def get_analytics_dashboard(db: AsyncSession = Depends(get_db)):
    # Total jobs
    total_jobs_res = await db.execute(select(func.count(Job.id)))
    total_jobs = total_jobs_res.scalar() or 0

    # Jobs today
    today_start = datetime.datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    jobs_today_res = await db.execute(select(func.count(Job.id)).where(Job.created_at >= today_start))
    jobs_today = jobs_today_res.scalar() or 0

    # Saved searches
    searches_res = await db.execute(select(func.count(SavedSearch.id)).where(SavedSearch.is_active == True))
    active_searches = searches_res.scalar() or 0

    # Notifications sent
    notifs_res = await db.execute(select(func.count(NotificationLog.id)))
    notifications_sent = notifs_res.scalar() or 0

    # Unique companies
    companies_res = await db.execute(select(func.count(func.distinct(Job.company))))
    companies_tracked = companies_res.scalar() or 0

    # Bookmarks
    bookmarks_res = await db.execute(select(func.count(Bookmark.id)))
    bookmarks_count = bookmarks_res.scalar() or 0

    # Top companies
    top_comp_stmt = select(Job.company, func.count(Job.id).label("count")).group_by(Job.company).order_by(func.count(Job.id).desc()).limit(5)
    top_comp_res = await db.execute(top_comp_stmt)
    top_companies = [{"company": r[0], "count": r[1]} for r in top_comp_res.all()]

    return {
        "success": True,
        "message": "Analytics dashboard data fetched.",
        "data": {
            "total_jobs": total_jobs,
            "jobs_discovered_today": jobs_today,
            "active_saved_searches": active_searches,
            "notifications_sent": notifications_sent,
            "companies_tracked": companies_tracked,
            "bookmarked_jobs": bookmarks_count,
            "top_hiring_companies": top_companies
        }
    }
