import datetime
import hashlib
import uuid
from typing import Optional, List
from fastapi import APIRouter, Depends, Query, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func, desc, or_

from backend.app.database import get_db
from backend.app.models.job import Job, Bookmark, ApplicationTracker, User
from backend.app.api.auth import get_current_user_optional
from backend.app.models.search_request import SearchRequest
from backend.app.engine.search import SearchEngine
from backend.app.engine.normalizer import NormalizerEngine, URLNormalizerValidator
from backend.app.engine.deduplicator import DeduplicatorEngine
from backend.app.engine.scheduler import SchedulerEngine
from backend.app.connectors.registry import connector_registry


router = APIRouter(prefix="/jobs", tags=["Jobs"])


class ManualJobCreate(BaseModel):
    title: str = Field(..., min_length=2, max_length=255, description="Job title, e.g. Senior Backend Engineer")
    company: str = Field(..., min_length=2, max_length=255, description="Company name, e.g. Stripe, OpenAI")
    job_url: str = Field(..., min_length=4, description="Direct application link or career URL")
    external_apply_url: Optional[str] = None
    location: Optional[str] = Field("Bengaluru, India", description="Job location")
    country: Optional[str] = "India"
    remote_type: Optional[str] = Field("Hybrid", description="Remote, Hybrid, On-site")
    employment_type: Optional[str] = Field("Full-time", description="Full-time, Internship, Contract")
    experience_level: Optional[str] = Field("Fresher", description="Fresher, Campus Hiring, Internship, Associate, Mid-Level, Senior, Lead")
    salary_range: Optional[str] = None
    min_salary_lpa: Optional[float] = None
    max_salary_lpa: Optional[float] = None
    department: Optional[str] = "Engineering"
    tags: Optional[str] = None
    skills: Optional[str] = None
    description: Optional[str] = None


@router.post("/manual", status_code=status.HTTP_201_CREATED)
@router.post("/create", status_code=status.HTTP_201_CREATED)
async def create_manual_job(
    req: ManualJobCreate,
    current_user: Optional[User] = Depends(get_current_user_optional),
    db: AsyncSession = Depends(get_db)
):
    """
    Admin / Recruiter endpoint to manually post new job listings / links.
    Immediately normalizes, validates, fingerprints, and indexes the job into the active database.
    """
    raw_title = req.title.strip()
    norm_title = NormalizerEngine.normalize_title(raw_title)

    # URL Validation & Normalization
    raw_url = req.job_url.strip()
    if not (raw_url.startswith("http://") or raw_url.startswith("https://")):
        raw_url = f"https://{raw_url}"
    clean_job_url = URLNormalizerValidator.strip_tracking_params(raw_url)

    clean_apply_url = None
    if req.external_apply_url and req.external_apply_url.strip():
        raw_apply = req.external_apply_url.strip()
        if not (raw_apply.startswith("http://") or raw_apply.startswith("https://")):
            raw_apply = f"https://{raw_apply}"
        clean_apply_url = URLNormalizerValidator.strip_tracking_params(raw_apply)

    # Experience level detection / assignment
    exp_level = NormalizerEngine.detect_experience_level(
        norm_title,
        req.description or "",
        explicit_level=req.experience_level
    )

    # Salary normalization
    min_sal = req.min_salary_lpa
    max_sal = req.max_salary_lpa
    salary_fmt = req.salary_range

    if req.salary_range and not (min_sal and max_sal):
        parsed_fmt, p_min, p_max = NormalizerEngine.parse_salary(req.salary_range, norm_title)
        if parsed_fmt:
            salary_fmt = parsed_fmt
        if p_min is not None and min_sal is None:
            min_sal = p_min
        if p_max is not None and max_sal is None:
            max_sal = p_max
    elif min_sal is not None or max_sal is not None:
        if min_sal is not None and max_sal is not None and min_sal != max_sal:
            salary_fmt = f"₹{min_sal:g} - ₹{max_sal:g} LPA"
        elif min_sal is not None:
            salary_fmt = f"₹{min_sal:g}+ LPA"
        elif max_sal is not None:
            salary_fmt = f"Up to ₹{max_sal:g} LPA"

    # Tags & Skills extraction
    tag_list = []
    if req.tags and req.tags.strip():
        tag_list = [t.strip() for t in req.tags.split(",") if t.strip()]
    elif req.skills and req.skills.strip():
        tag_list = [t.strip() for t in req.skills.split(",") if t.strip()]
    else:
        tag_list = NormalizerEngine.extract_tags(norm_title, req.description or "")

    raw_tags_str = ", ".join(tag_list) if tag_list else "Tech, Software Engineering"

    # Fingerprint generation
    norm_company = req.company.strip()
    norm_location = (req.location or "Bengaluru, India").strip()
    fp_raw = f"manual:{norm_company.lower()}:{norm_title.lower()}:{clean_job_url.lower()}"
    fp = hashlib.sha256(fp_raw.encode("utf-8")).hexdigest()

    now = datetime.datetime.utcnow()

    # Check for existing job by fingerprint or exact URL
    res_existing = await db.execute(
        select(Job).where(
            or_(
                Job.hash_signature == fp,
                Job.job_url == clean_job_url
            )
        )
    )
    existing_job = res_existing.scalars().first()

    if existing_job:
        # Update and reactivate
        existing_job.title = norm_title
        existing_job.company = norm_company
        existing_job.department = req.department or existing_job.department
        existing_job.location = norm_location
        existing_job.remote_type = req.remote_type or existing_job.remote_type
        existing_job.employment_type = req.employment_type or existing_job.employment_type
        existing_job.experience_level = exp_level
        if salary_fmt:
            existing_job.salary_range = salary_fmt
            existing_job.min_salary_lpa = min_sal
            existing_job.max_salary_lpa = max_sal
        existing_job.external_apply_url = clean_apply_url or existing_job.external_apply_url
        existing_job.raw_tags = raw_tags_str
        existing_job.skills = raw_tags_str
        if req.description:
            existing_job.description = req.description
        existing_job.status = "ACTIVE"
        existing_job.verification_status = "VERIFIED"
        existing_job.last_seen = now
        existing_job.last_verified = now
        existing_job.consecutive_missing_count = 0
        job_entity = existing_job
    else:
        ext_id = f"manual_{uuid.uuid4().hex[:10]}"
        job_entity = Job(
            external_job_id=ext_id,
            title=norm_title,
            company=norm_company,
            department=req.department or "Engineering",
            location=norm_location,
            country=req.country or "India",
            remote_type=req.remote_type or "Hybrid",
            employment_type=req.employment_type or "Full-time",
            experience_level=exp_level,
            salary_range=salary_fmt,
            min_salary_lpa=min_sal,
            max_salary_lpa=max_sal,
            currency="INR",
            job_url=clean_job_url,
            source_url=clean_job_url,
            external_apply_url=clean_apply_url or clean_job_url,
            apply_url=clean_apply_url or clean_job_url,
            canonical_url=clean_job_url,
            source="Admin Manual",
            source_type="Direct",
            raw_tags=raw_tags_str,
            skills=raw_tags_str,
            benefits="Direct Admin Posting",
            description=req.description or f"Direct opportunity at {norm_company} for {norm_title}.",
            hash_signature=fp,
            status="ACTIVE",
            verification_status="VERIFIED",
            first_seen=now,
            last_seen=now,
            last_verified=now,
            consecutive_missing_count=0,
            posted_at=now,
            discovered_at=now,
            created_at=now
        )
        db.add(job_entity)

    await db.commit()
    await db.refresh(job_entity)

    return {
        "success": True,
        "message": f"Job opportunity '{norm_title}' at '{norm_company}' has been published successfully.",
        "data": {
            "id": job_entity.id,
            "external_job_id": job_entity.external_job_id,
            "title": job_entity.title,
            "company": job_entity.company,
            "department": job_entity.department,
            "location": job_entity.location,
            "remote_type": job_entity.remote_type,
            "employment_type": job_entity.employment_type,
            "experience_level": job_entity.experience_level,
            "salary_range": job_entity.salary_range,
            "min_salary_lpa": job_entity.min_salary_lpa,
            "max_salary_lpa": job_entity.max_salary_lpa,
            "job_url": job_entity.job_url,
            "external_apply_url": job_entity.external_apply_url,
            "source": job_entity.source,
            "source_type": job_entity.source_type,
            "tags": job_entity.raw_tags.split(", ") if job_entity.raw_tags else [],
            "raw_tags": job_entity.raw_tags,
            "description": job_entity.description,
            "status": job_entity.status,
            "verification_status": job_entity.verification_status,
            "first_seen": job_entity.first_seen.isoformat() if job_entity.first_seen else None,
            "last_seen": job_entity.last_seen.isoformat() if job_entity.last_seen else None,
            "posted_at": job_entity.posted_at.isoformat() if job_entity.posted_at else None
        }
    }


@router.delete("/{job_id}")
async def delete_job(
    job_id: int,
    current_user: Optional[User] = Depends(get_current_user_optional),
    db: AsyncSession = Depends(get_db)
):
    """
    Allows admins / users to delete or unlist a job listing from the portal.
    """
    res = await db.execute(select(Job).where(Job.id == job_id))
    job = res.scalars().first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    job_title = job.title
    job.status = "REMOVED"
    job.closed_at = datetime.datetime.utcnow()
    job.closure_reason = "Manual Admin Removal"
    await db.commit()

    return {
        "success": True,
        "message": f"Job #{job_id} ({job_title}) has been unlisted from the portal."
    }


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
    User-Driven Search Endpoint with Database Fallback & Real-time Integration
    Constructs a SearchRequest object from user parameters and dispatches to connectors.
    Combines live connector search with active database records (including manual admin postings).
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

        # Cross-reference live connector search results against database to exclude REMOVED listings
        if deduped_jobs:
            fps = [j.get("hash_signature") or DeduplicatorEngine.generate_fingerprint(j) for j in deduped_jobs]
            res_db_status = await db.execute(select(Job.hash_signature, Job.status).where(Job.hash_signature.in_(fps)))
            non_active_fps = {row[0] for row in res_db_status.all() if row[1] != "ACTIVE"}
            deduped_jobs = [
                j for j in deduped_jobs
                if (j.get("hash_signature") or DeduplicatorEngine.generate_fingerprint(j)) not in non_active_fps
            ]

        # Also query active database jobs that match the keyword/filters
        stmt_db_match = select(Job).where(Job.status == "ACTIVE")
        boolean_cond = SearchEngine.build_boolean_conditions(keyword)
        if boolean_cond is not None:
            stmt_db_match = stmt_db_match.where(boolean_cond)
        else:
            stmt_db_match = stmt_db_match.where(
                or_(
                    Job.title.ilike(f"%{keyword}%"),
                    Job.company.ilike(f"%{keyword}%"),
                    Job.raw_tags.ilike(f"%{keyword}%")
                )
            )

        if location:
            stmt_db_match = stmt_db_match.where(Job.location.ilike(f"%{location}%"))
        if remote_type:
            stmt_db_match = stmt_db_match.where(Job.remote_type.ilike(f"%{remote_type}%"))
        if experience_level:
            stmt_db_match = stmt_db_match.where(Job.experience_level.ilike(f"%{experience_level}%"))
        if salary_min:
            stmt_db_match = stmt_db_match.where(Job.min_salary_lpa >= salary_min)

        res_matching_db = await db.execute(stmt_db_match.order_by(desc(Job.last_seen), desc(Job.id)).limit(limit))
        db_matched_jobs = res_matching_db.scalars().all()

        formatted_db_matched = [
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
                "hash_signature": j.hash_signature,
                "is_bookmarked": j.is_bookmarked,
                "status": j.status,
                "verification_status": j.verification_status,
                "first_seen": j.first_seen.isoformat() if j.first_seen else None,
                "last_seen": j.last_seen.isoformat() if j.last_seen else None,
                "last_verified": j.last_verified.isoformat() if j.last_verified else None,
                "posted_at": j.posted_at.isoformat() if j.posted_at else None
            }
            for j in db_matched_jobs
        ]

        # Combine DB matches (prioritizing manual admin & latest seen) with connector results
        combined_jobs = formatted_db_matched + deduped_jobs
        seen_fps = set()
        final_search_jobs = []
        for j in combined_jobs:
            fp = j.get("hash_signature") or DeduplicatorEngine.generate_fingerprint(j)
            if fp not in seen_fps:
                seen_fps.add(fp)
                final_search_jobs.append(j)

        if final_search_jobs:
            return {
                "success": True,
                "query": req.to_dict(),
                "meta": {
                    "total_records": len(final_search_jobs),
                    "page": page,
                    "limit": limit,
                    "total_pages": max(1, (len(final_search_jobs) + limit - 1) // limit)
                },
                "data": final_search_jobs[:limit]
            }

    # DB Fallback query for seamless discovery feed when live search returns 0 or empty keyword
    stmt = select(Job).where(Job.status == "ACTIVE")
    if keyword:
        boolean_cond = SearchEngine.build_boolean_conditions(keyword)
        if boolean_cond is not None:
            stmt = stmt.where(boolean_cond)
        else:
            stmt = stmt.where(
                or_(
                    Job.title.ilike(f"%{keyword}%"),
                    Job.company.ilike(f"%{keyword}%"),
                    Job.raw_tags.ilike(f"%{keyword}%")
                )
            )
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
    stmt = stmt.order_by(desc(Job.last_seen), desc(Job.id)).offset(offset).limit(limit)
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

    if status and status.strip() and status.strip().upper() != "ALL":
        stmt = stmt.where(Job.status.ilike(f"%{status.strip()}%"))
    else:
        stmt = stmt.where(Job.status == "ACTIVE")

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
    stmt = stmt.order_by(desc(Job.last_seen), desc(Job.id)).offset(offset).limit(limit)

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
            "hash_signature": j.hash_signature,
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

@router.get("/{job_id}")
async def get_job_detail(
    job_id: int,
    db: AsyncSession = Depends(get_db)
):
    res = await db.execute(select(Job).where(Job.id == job_id))
    j = res.scalars().first()
    if not j:
        raise HTTPException(status_code=404, detail="Job not found")

    is_active = (j.status == "ACTIVE")
    return {
        "success": True,
        "data": {
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
            "source": j.source,
            "source_type": j.source_type,
            "tags": j.raw_tags.split(", ") if j.raw_tags else [],
            "raw_tags": j.raw_tags,
            "description": j.description,
            "is_bookmarked": j.is_bookmarked,
            "status": j.status,
            "verification_status": j.verification_status,
            "is_active_opportunity": is_active,
            "notice": None if is_active else "This job is no longer active.",
            "first_seen": j.first_seen.isoformat() if j.first_seen else None,
            "last_seen": j.last_seen.isoformat() if j.last_seen else None,
            "last_verified": j.last_verified.isoformat() if j.last_verified else None,
            "posted_at": j.posted_at.isoformat() if j.posted_at else None
        }
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

