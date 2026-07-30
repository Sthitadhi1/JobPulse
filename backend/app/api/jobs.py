from typing import Optional, List
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func, desc, or_

from backend.app.database import get_db
from backend.app.models.job import Job, Bookmark, ApplicationTracker
from backend.app.engine.search import SearchEngine

router = APIRouter(prefix="/jobs", tags=["Jobs"])

@router.get("")
async def list_jobs(
    q: Optional[str] = Query(None, description="Search query string with optional Boolean operators (AND, OR, NOT)"),
    location: Optional[str] = Query(None),
    remote_type: Optional[str] = Query(None),
    experience_level: Optional[str] = Query(None),
    min_salary_lpa: Optional[float] = Query(None),
    company: Optional[str] = Query(None),
    source: Optional[str] = Query(None),
    bookmarked_only: Optional[bool] = Query(False),
    india_or_remote_only: Optional[bool] = Query(True, description="Default filter to India & Remote opportunities"),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db)
):
    stmt = select(Job)

    # Boolean search filter
    if q:
        boolean_cond = SearchEngine.build_boolean_conditions(q)
        if boolean_cond is not None:
            stmt = stmt.where(boolean_cond)

    if india_or_remote_only and not location:
        india_keywords = ["india", "bengaluru", "bangalore", "hyderabad", "pune", "mumbai", "gurugram", "gurgaon", "noida", "chennai", "delhi", "remote", "worldwide"]
        conds = [Job.location.ilike(f"%{k}%") for k in india_keywords]
        conds.append(Job.remote_type == "Remote")
        stmt = stmt.where(or_(*conds))

    if location:
        stmt = stmt.where(Job.location.ilike(f"%{location}%"))
    if remote_type:
        stmt = stmt.where(Job.remote_type.ilike(f"%{remote_type}%"))
    if experience_level:
        exp_lower = experience_level.lower()
        if any(k in exp_lower for k in ["fresher", "fresh", "0-1", "entry"]):
            stmt = stmt.where(or_(
                Job.experience_level.ilike("%Fresher%"),
                Job.experience_level.ilike("%Fresh%"),
                Job.experience_level.ilike("%0-1%"),
                Job.experience_level.ilike("%Internship%"),
                Job.experience_level.ilike("%0-2%")
            ))
        elif any(k in exp_lower for k in ["2-4", "mid"]):
            stmt = stmt.where(or_(
                Job.experience_level.ilike("%2-4%"),
                Job.experience_level.ilike("%Mid%")
            ))
        elif any(k in exp_lower for k in ["4+", "high", "senior"]):
            stmt = stmt.where(or_(
                Job.experience_level.ilike("%4+%"),
                Job.experience_level.ilike("%High%"),
                Job.experience_level.ilike("%Senior%")
            ))
        else:
            stmt = stmt.where(Job.experience_level.ilike(f"%{experience_level}%"))
    if min_salary_lpa:
        stmt = stmt.where(Job.min_salary_lpa >= min_salary_lpa)
    if company:
        stmt = stmt.where(Job.company.ilike(f"%{company}%"))
    if source:
        stmt = stmt.where(Job.source.ilike(f"%{source}%"))
    if bookmarked_only:
        stmt = stmt.where(Job.is_bookmarked == True)

    # Count total
    count_stmt = select(func.count()).select_from(stmt.subquery())
    total_res = await db.execute(count_stmt)
    total_records = total_res.scalar() or 0

    # Paginate
    offset = (page - 1) * limit
    stmt = stmt.order_by(desc(Job.created_at), desc(Job.id)).offset(offset).limit(limit)

    res = await db.execute(stmt)
    jobs = res.scalars().all()

    # Format output
    job_list = []
    for j in jobs:
        job_list.append({
            "id": j.id,
            "title": j.title,
            "company": j.company,
            "location": j.location,
            "remote_type": j.remote_type,
            "employment_type": j.employment_type,
            "experience_level": j.experience_level,
            "salary_range": j.salary_range,
            "min_salary_lpa": j.min_salary_lpa,
            "max_salary_lpa": j.max_salary_lpa,
            "url": j.apply_url,
            "source": j.source,
            "tags": j.raw_tags.split(", ") if j.raw_tags else [],
            "description": j.description,
            "is_bookmarked": j.is_bookmarked,
            "posted_at": j.posted_at.isoformat() if j.posted_at else None,
            "created_at": j.created_at.isoformat() if j.created_at else None
        })

    return {
        "success": True,
        "message": "Jobs fetched successfully.",
        "data": job_list,
        "meta": {
            "page": page,
            "limit": limit,
            "total_records": total_records,
            "total_pages": (total_records + limit - 1) // limit if limit else 1
        }
    }

@router.get("/{job_id}")
async def get_job_detail(job_id: int, db: AsyncSession = Depends(get_db)):
    res = await db.execute(select(Job).where(Job.id == job_id))
    job = res.scalars().first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found.")
    
    return {
        "success": True,
        "message": "Job details fetched.",
        "data": {
            "id": job.id,
            "title": job.title,
            "company": job.company,
            "location": job.location,
            "remote_type": job.remote_type,
            "employment_type": job.employment_type,
            "experience_level": job.experience_level,
            "salary_range": job.salary_range,
            "min_salary_lpa": job.min_salary_lpa,
            "max_salary_lpa": job.max_salary_lpa,
            "url": job.apply_url,
            "source": job.source,
            "tags": job.raw_tags.split(", ") if job.raw_tags else [],
            "description": job.description,
            "is_bookmarked": job.is_bookmarked,
            "posted_at": job.posted_at.isoformat() if job.posted_at else None
        }
    }

@router.post("/{job_id}/bookmark")
async def toggle_bookmark(job_id: int, db: AsyncSession = Depends(get_db)):
    res = await db.execute(select(Job).where(Job.id == job_id))
    job = res.scalars().first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found.")

    job.is_bookmarked = not job.is_bookmarked

    if job.is_bookmarked:
        bm = Bookmark(job_id=job.id, folder="Interested", notes="Bookmarked via Dashboard")
        db.add(bm)
        app_track = ApplicationTracker(job_id=job.id, company=job.company, role=job.title, status="Interested")
        db.add(app_track)

    await db.commit()
    return {
        "success": True,
        "message": f"Job bookmark {'added' if job.is_bookmarked else 'removed'}.",
        "data": {"id": job.id, "is_bookmarked": job.is_bookmarked}
    }
