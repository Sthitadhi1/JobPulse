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
    source_type: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    verification_status: Optional[str] = Query(None),
    bookmarked_only: Optional[bool] = Query(False),
    india_or_remote_only: Optional[bool] = Query(False, description="Default filter to India & Remote opportunities"),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db)
):
    stmt = select(Job)

    # Filter out removed jobs by default unless requested
    if status:
        stmt = stmt.where(Job.status.ilike(f"%{status}%"))
    else:
        stmt = stmt.where(Job.status != "REMOVED")

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
    
    # PART 14 — Experience Level Search Guardrail
    if experience_level:
        exp_lower = experience_level.lower()
        if "fresher" in exp_lower or "0-1" in exp_lower:
            # ONLY return genuine freshers, campus hiring, internships, entry-level! Never 2+ yoe!
            stmt = stmt.where(or_(
                Job.experience_level == "Fresher",
                Job.experience_level == "Campus Hiring",
                Job.experience_level == "Internship",
                Job.experience_level == "Fresher / 0-1 YOE"
            ))
        elif "intern" in exp_lower:
            stmt = stmt.where(Job.experience_level == "Internship")
        elif "campus" in exp_lower:
            stmt = stmt.where(Job.experience_level == "Campus Hiring")
        elif "associate" in exp_lower:
            stmt = stmt.where(Job.experience_level == "Associate")
        elif "mid" in exp_lower or "2-4" in exp_lower:
            stmt = stmt.where(or_(
                Job.experience_level == "Mid-Level",
                Job.experience_level == "2-4 YOE (Mid Level)"
            ))
        elif "senior" in exp_lower or "4+" in exp_lower:
            stmt = stmt.where(or_(
                Job.experience_level == "Senior",
                Job.experience_level == "Lead",
                Job.experience_level == "4+ YOE (High Exp)"
            ))
        else:
            stmt = stmt.where(Job.experience_level.ilike(f"%{experience_level}%"))

    if min_salary_lpa:
        stmt = stmt.where(Job.min_salary_lpa >= min_salary_lpa)
    if company:
        stmt = stmt.where(Job.company.ilike(f"%{company}%"))
    if source:
        stmt = stmt.where(Job.source.ilike(f"%{source}%"))
    if source_type:
        stmt = stmt.where(Job.source_type.ilike(f"%{source_type}%"))
    if verification_status:
        stmt = stmt.where(Job.verification_status.ilike(f"%{verification_status}%"))
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

    # Format output with verification badges and smart apply URLs (PART 9 & 10)
    job_list = []
    for j in jobs:
        smart_url = j.external_apply_url or j.job_url or j.source_url or j.apply_url
        job_list.append({
            "id": j.id,
            "title": j.title,
            "company": j.company,
            "department": j.department,
            "location": j.location,
            "country": j.country or "India",
            "remote_type": j.remote_type,
            "employment_type": j.employment_type,
            "experience_level": j.experience_level,
            "salary_range": j.salary_range,
            "min_salary_lpa": j.min_salary_lpa,
            "max_salary_lpa": j.max_salary_lpa,
            "job_url": j.job_url or j.apply_url,
            "source_url": j.source_url or j.apply_url,
            "external_apply_url": j.external_apply_url,
            "url": smart_url if smart_url and smart_url != "#" else None, # Smart Apply Target
            "source": j.source,
            "source_type": j.source_type or "ATS",
            "tags": j.raw_tags.split(", ") if j.raw_tags else [],
            "skills": j.skills,
            "benefits": j.benefits,
            "description": j.description,
            "status": j.status or "ACTIVE",
            "verification_status": j.verification_status or "VERIFIED",
            "verification_count": j.verification_count or 1,
            "first_seen": j.first_seen.isoformat() if j.first_seen else (j.created_at.isoformat() if j.created_at else None),
            "last_seen": j.last_seen.isoformat() if j.last_seen else (j.created_at.isoformat() if j.created_at else None),
            "last_verified": j.last_verified.isoformat() if j.last_verified else (j.created_at.isoformat() if j.created_at else None),
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
    
    smart_url = job.external_apply_url or job.job_url or job.source_url or job.apply_url
    return {
        "success": True,
        "message": "Job details fetched.",
        "data": {
            "id": job.id,
            "title": job.title,
            "company": job.company,
            "department": job.department,
            "location": job.location,
            "country": job.country or "India",
            "remote_type": job.remote_type,
            "employment_type": job.employment_type,
            "experience_level": job.experience_level,
            "salary_range": job.salary_range,
            "min_salary_lpa": job.min_salary_lpa,
            "max_salary_lpa": job.max_salary_lpa,
            "job_url": job.job_url or job.apply_url,
            "source_url": job.source_url or job.apply_url,
            "external_apply_url": job.external_apply_url,
            "url": smart_url if smart_url and smart_url != "#" else None,
            "source": job.source,
            "source_type": job.source_type or "ATS",
            "tags": job.raw_tags.split(", ") if job.raw_tags else [],
            "skills": job.skills,
            "benefits": job.benefits,
            "description": job.description,
            "status": job.status or "ACTIVE",
            "verification_status": job.verification_status or "VERIFIED",
            "verification_count": job.verification_count or 1,
            "first_seen": job.first_seen.isoformat() if job.first_seen else (job.created_at.isoformat() if job.created_at else None),
            "last_verified": job.last_verified.isoformat() if job.last_verified else (job.created_at.isoformat() if job.created_at else None),
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
