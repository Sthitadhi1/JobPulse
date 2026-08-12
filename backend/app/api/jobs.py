from typing import Optional, List
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func, desc, or_

from backend.app.database import get_db
from backend.app.models.job import Job, Bookmark, ApplicationTracker, User
from backend.app.api.auth import get_current_user_optional
from backend.app.models.search_request import SearchRequest
from backend.app.engine.search import SearchEngine
from backend.app.engine.normalizer import NormalizerEngine
from backend.app.engine.deduplicator import DeduplicatorEngine
from backend.app.engine.scheduler import SchedulerEngine
from backend.app.connectors.registry import connector_registry


router = APIRouter(prefix="/jobs", tags=["Jobs"])

@router.get("/search")
async def user_search_jobs(
    keyword: Optional[str] = Query(None, description="Job title or technology keyword e.g. Machine Learning"),
    location: Optional[str] = Query(None, description="Location e.g. Bangalore"),
    salary_min: Optional[float] = Query(None),
    salary_max: Optional[float] = Query(None),
    experience_level: Optional[str] = Query(None),
    employment_type: Optional[str] = Query(None),
    remote_type: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db)
):
    """
    PART 1 & 6 — User-Driven Search Endpoint with Database Fallback
    Constructs a SearchRequest object from user parameters and dispatches to connectors.
    If live search yields 0 jobs (or empty keyword), falls back to active database records.
    """
    req = SearchRequest(
        keyword=keyword,
        location=location,
        min_salary_lpa=salary_min,
        max_salary_lpa=salary_max,
        experience_level=experience_level,
        employment_type=employment_type,
        remote_type=remote_type,
        page=page,
        limit=limit
    )

    deduped_jobs = []
    if keyword and keyword.strip():
        raw_results = await connector_registry.run_user_search(req)
        normalized = [NormalizerEngine.normalize_job_data(j) for j in raw_results]
        valid_jobs = [j for j in normalized if SchedulerEngine.validate_job_data(j)]
        deduped_jobs = DeduplicatorEngine.deduplicate_in_memory(valid_jobs)

    if deduped_jobs:
        return {
            "success": True,
            "query": req.to_dict(),
            "meta": {
                "total_records": len(deduped_jobs),
                "page": page,
                "limit": limit,
                "total_pages": max(1, (len(deduped_jobs) + limit - 1) // limit)
            },
            "data": deduped_jobs[:limit]
        }

    # DB Fallback query for seamless discovery feed when live search returns 0
    stmt = select(Job).where(Job.status == "ACTIVE")
    if keyword:
        boolean_cond = SearchEngine.build_boolean_conditions(keyword)
        if boolean_cond is not None:
            stmt = stmt.where(boolean_cond)
        else:
            stmt = stmt.where(Job.title.ilike(f"%{keyword}%"))
    if location:
        stmt = stmt.where(Job.location.ilike(f"%{location}%"))
    if remote_type:
        stmt = stmt.where(Job.remote_type.ilike(f"%{remote_type}%"))
    if experience_level:
        stmt = stmt.where(Job.experience_level.ilike(f"%{experience_level}%"))
    if salary_min:
        stmt = stmt.where(Job.min_salary_lpa >= salary_min)

    total_db_res = await db.execute(select(func.count()).select_from(stmt.subquery()))
    total_db_records = total_db_res.scalar() or 0

    offset = (page - 1) * limit
    stmt = stmt.order_by(desc(Job.posted_at), desc(Job.id)).offset(offset).limit(limit)
    db_res = await db.execute(stmt)
    db_jobs = db_res.scalars().all()

    formatted_db_jobs = [
        {
            "id": j.id,
            "external_job_id": j.external_job_id,
            "title": j.title,
            "company": j.company,
            "department": j.department,
            "location": j.location,
            "country": j.country,
            "remote_type": j.remote_type,
            "employment_type": j.employment_type,
            "experience_level": j.experience_level,
            "salary_range": j.salary_range,
            "min_salary_lpa": j.min_salary_lpa,
            "max_salary_lpa": j.max_salary_lpa,
            "job_url": j.job_url,
            "source_url": j.source_url,
            "external_apply_url": j.external_apply_url,
            "url": j.job_url,
            "source": j.source,
            "source_type": j.source_type,
            "tags": j.raw_tags.split(", ") if j.raw_tags else [],
            "raw_tags": j.raw_tags,
            "description": j.description,
            "is_bookmarked": j.is_bookmarked,
            "status": j.status,
            "verification_status": j.verification_status,
            "first_seen": j.first_seen.isoformat() if j.first_seen else None,
            "last_seen": j.last_seen.isoformat() if j.last_seen else None,
            "last_verified": j.last_verified.isoformat() if j.last_verified else None,
            "posted_at": j.posted_at.isoformat() if j.posted_at else None
        }
        for j in db_jobs
    ]

    return {
        "success": True,
        "query": req.to_dict(),
        "meta": {
            "total_records": total_db_records,
            "page": page,
            "limit": limit,
            "total_pages": max(1, (total_db_records + limit - 1) // limit)
        },
        "data": formatted_db_jobs
    }

@router.get("")
async def list_jobs(
    q: Optional[str] = Query(None, description="Search query string with optional Boolean operators (AND, OR, NOT)"),
    location: Optional[str] = Query(None),
    remote_type: Optional[str] = Query(None),
    experience_level: Optional[str] = Query(None),
    min_salary_lpa: Optional[float] = Query(None),
    company: Optional[str] = Query(None),
    department: Optional[str] = Query(None),
    source: Optional[str] = Query(None),
    source_type: Optional[str] = Query(None),
    ats_provider: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    verification_status: Optional[str] = Query(None),
    bookmarked_only: Optional[bool] = Query(False),
    india_or_remote_only: Optional[bool] = Query(False),
    page: int = Query(1, ge=1),
    limit: int = Query(30, ge=1, le=100),
    current_user: Optional[User] = Depends(get_current_user_optional),
    db: AsyncSession = Depends(get_db)
):

    stmt = select(Job)

    if status:
        stmt = stmt.where(Job.status.ilike(f"%{status}%"))
    else:
        stmt = stmt.where(Job.status != "REMOVED")

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
        if "fresher" in exp_lower or "0-1" in exp_lower:
            stmt = stmt.where(Job.experience_level.in_(["Fresher", "Campus Hiring", "Internship", "Associate"]))
        else:
            stmt = stmt.where(Job.experience_level.ilike(f"%{experience_level}%"))

    if min_salary_lpa:
        stmt = stmt.where(Job.min_salary_lpa >= min_salary_lpa)
    if company:
        stmt = stmt.where(Job.company.ilike(f"%{company}%"))
    if department:
        stmt = stmt.where(Job.department.ilike(f"%{department}%"))
    if source:
        stmt = stmt.where(Job.source.ilike(f"%{source}%"))
    if source_type:
        stmt = stmt.where(Job.source_type.ilike(f"%{source_type}%"))
    if verification_status:
        stmt = stmt.where(Job.verification_status == verification_status)

    if bookmarked_only:
        if current_user:
            stmt = stmt.join(Bookmark, Bookmark.job_id == Job.id).where(Bookmark.user_id == current_user.id)
        else:
            stmt = stmt.where(Job.is_bookmarked == True)

    total_res = await db.execute(select(func.count()).select_from(stmt.subquery()))
    total_records = total_res.scalar() or 0

    offset = (page - 1) * limit
    stmt = stmt.order_by(desc(Job.posted_at), desc(Job.id)).offset(offset).limit(limit)

    res = await db.execute(stmt)
    jobs = res.scalars().all()

    formatted_jobs = [
        {
            "id": j.id,
            "external_job_id": j.external_job_id,
            "title": j.title,
            "company": j.company,
            "department": j.department,
            "location": j.location,
            "country": j.country,
            "remote_type": j.remote_type,
            "employment_type": j.employment_type,
            "experience_level": j.experience_level,
            "salary_range": j.salary_range,
            "min_salary_lpa": j.min_salary_lpa,
            "max_salary_lpa": j.max_salary_lpa,
            "job_url": j.job_url,
            "source_url": j.source_url,
            "external_apply_url": j.external_apply_url,
            "url": j.job_url,
            "source": j.source,
            "source_type": j.source_type,
            "tags": j.raw_tags.split(", ") if j.raw_tags else [],
            "raw_tags": j.raw_tags,
            "description": j.description,
            "is_bookmarked": j.is_bookmarked,
            "status": j.status,
            "verification_status": j.verification_status,
            "first_seen": j.first_seen.isoformat() if j.first_seen else None,
            "last_seen": j.last_seen.isoformat() if j.last_seen else None,
            "last_verified": j.last_verified.isoformat() if j.last_verified else None,
            "posted_at": j.posted_at.isoformat() if j.posted_at else None
        }
        for j in jobs
    ]

    return {
        "success": True,
        "meta": {
            "total_records": total_records,
            "page": page,
            "limit": limit,
            "total_pages": max(1, (total_records + limit - 1) // limit)
        },
        "data": formatted_jobs
    }

@router.post("/{job_id}/bookmark")
async def toggle_bookmark(
    job_id: int,
    current_user: Optional[User] = Depends(get_current_user_optional),
    db: AsyncSession = Depends(get_db)
):
    res = await db.execute(select(Job).where(Job.id == job_id))
    job = res.scalars().first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    user_id = current_user.id if current_user else None

    if user_id:
        bm_res = await db.execute(select(Bookmark).where(Bookmark.job_id == job_id, Bookmark.user_id == user_id))
        bm = bm_res.scalars().first()
        if bm:
            await db.delete(bm)
            is_bookmarked = False
        else:
            new_bm = Bookmark(job_id=job_id, user_id=user_id)
            db.add(new_bm)
            is_bookmarked = True
        job.is_bookmarked = is_bookmarked
    else:
        job.is_bookmarked = not job.is_bookmarked
        is_bookmarked = job.is_bookmarked

    await db.commit()

    return {
        "success": True,
        "data": {
            "id": job.id,
            "is_bookmarked": is_bookmarked
        }
    }

