import hashlib
import datetime
import re
from typing import Dict, Any, List, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from backend.app.models.job import Job

class DeduplicatorEngine:
    @staticmethod
    def generate_fingerprint(job: Dict[str, Any]) -> str:
        """
        PART 11 — Duplicate Detection 4-Tier Hierarchy:
        1. External Job ID + Company
        2. Canonical URL / Clean Job URL
        3. Company + Title
        4. Company + Title + Location
        """
        ext_id = job.get("external_job_id")
        job_url = job.get("job_url") or job.get("apply_url") or job.get("canonical_url") or ""
        company = job.get("company", "")
        title = job.get("title", "")
        location = job.get("location", "")

        clean_company = re.sub(r'[^a-z0-9]', '', company.lower())
        clean_title = re.sub(r'[^a-z0-9]', '', title.lower())
        clean_loc = re.sub(r'[^a-z0-9]', '', location.lower())

        if ext_id and str(ext_id).strip():
            raw_str = f"tier1:{clean_company}:{str(ext_id).strip()}"
        elif job_url and job_url != "#":
            clean_url = re.sub(r'^https?://', '', job_url.lower()).strip('/')
            clean_url = re.sub(r'\?.*$', '', clean_url)
            raw_str = f"tier2:{clean_url}"
        elif clean_company and clean_title:
            raw_str = f"tier3:{clean_company}:{clean_title}"
        else:
            raw_str = f"tier4:{clean_company}:{clean_title}:{clean_loc}"

        return hashlib.sha256(raw_str.encode('utf-8')).hexdigest()

    @classmethod
    def deduplicate_in_memory(cls, jobs_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Fast in-memory deduplication for live user search queries.
        Merges duplicate jobs originating from multiple sources into a single card.
        """
        seen = {}
        for job in jobs_data:
            fp = cls.generate_fingerprint(job)
            if fp not in seen:
                seen[fp] = job
            else:
                existing_source = seen[fp].get("source", "")
                if job.get("source") and job["source"] not in existing_source:
                    seen[fp]["source"] = f"{existing_source}, {job['source']}"
        return list(seen.values())

    @classmethod
    async def process_and_update_jobs(cls, db: AsyncSession, jobs_data: List[Dict[str, Any]]) -> Tuple[List[Dict[str, Any]], int]:
        if not jobs_data:
            return [], 0

        prepared_jobs = []
        fingerprints = []
        for job in jobs_data:
            fp = cls.generate_fingerprint(job)
            job["hash_signature"] = fp
            prepared_jobs.append(job)
            fingerprints.append(fp)

        existing_jobs = {}
        chunk_size = 100
        for i in range(0, len(fingerprints), chunk_size):
            chunk_fps = fingerprints[i:i + chunk_size]
            res = await db.execute(select(Job).where(Job.hash_signature.in_(chunk_fps)))
            for j in res.scalars().all():
                existing_jobs[j.hash_signature] = j

        new_jobs = []
        updated_count = 0
        now = datetime.datetime.utcnow()

        for job in prepared_jobs:
            fp = job["hash_signature"]
            if fp in existing_jobs:
                existing_j = existing_jobs[fp]
                existing_j.last_seen = now
                existing_j.last_verified = now
                if job.get("salary_range") and not existing_j.salary_range:
                    existing_j.salary_range = job["salary_range"]
                    existing_j.min_salary_lpa = job.get("min_salary_lpa")
                    existing_j.max_salary_lpa = job.get("max_salary_lpa")
                if job.get("external_apply_url") and not existing_j.external_apply_url:
                    existing_j.external_apply_url = job["external_apply_url"]
                updated_count += 1
            else:
                new_jobs.append(job)

        return new_jobs, updated_count

    @classmethod
    async def reconcile_connector_jobs(
        cls,
        db: AsyncSession,
        connector_name: str,
        jobs_data: List[Dict[str, Any]]
    ) -> Tuple[int, int, int, List[Job]]:
        """
        Source-specific reconciliation for a successful connector run.
        Updates matching active/removed jobs, inserts new jobs, and increments missing count
        for active jobs from this source that were not returned in this run.
        """
        from backend.app.config import settings
        threshold = getattr(settings, "JOB_MISSING_CYCLES_THRESHOLD", 2)
        now = datetime.datetime.utcnow()

        from sqlalchemy import or_
        from sqlalchemy.exc import IntegrityError

        source_names = {connector_name, f"{connector_name} Careers"}
        fps = []
        for j in jobs_data:
            if j.get("source"):
                source_names.add(j["source"])
            fp = j.get("hash_signature") or cls.generate_fingerprint(j)
            j["hash_signature"] = fp
            fps.append(fp)

        # Query existing jobs matching source variations or hash signatures
        stmt = select(Job).where(or_(Job.source.in_(list(source_names)), Job.hash_signature.in_(fps)))
        res = await db.execute(stmt)
        existing_jobs = res.scalars().all()

        ext_id_map = {}
        canonical_map = {}
        job_url_map = {}
        hash_map = {}

        for j in existing_jobs:
            if j.external_job_id:
                ext_id_map[str(j.external_job_id).strip()] = j
            if j.canonical_url:
                clean_canon = re.sub(r'^https?://', '', j.canonical_url.lower()).strip('/')
                if clean_canon:
                    canonical_map[clean_canon] = j
            if j.job_url and j.job_url != "#":
                clean_url = re.sub(r'^https?://', '', j.job_url.lower()).strip('/')
                if clean_url:
                    job_url_map[clean_url] = j
            if j.hash_signature:
                hash_map[j.hash_signature] = j

        matched_job_ids = set()
        inserted_count = 0
        updated_count = 0
        new_job_entities = []

        for job in jobs_data:
            fp = job.get("hash_signature") or cls.generate_fingerprint(job)
            job["hash_signature"] = fp

            ext_id = job.get("external_job_id")
            canon_url = job.get("canonical_url")
            raw_job_url = job.get("job_url") or job.get("apply_url") or ""

            clean_canon = re.sub(r'^https?://', '', canon_url.lower()).strip('/') if canon_url else ""
            clean_job_url = re.sub(r'^https?://', '', raw_job_url.lower()).strip('/') if raw_job_url and raw_job_url != "#" else ""

            matched_job = None
            # Priority 1: source + external_job_id
            if ext_id and str(ext_id).strip() in ext_id_map:
                matched_job = ext_id_map[str(ext_id).strip()]
            # Priority 2: source + canonical_url
            elif clean_canon and clean_canon in canonical_map:
                matched_job = canonical_map[clean_canon]
            # Priority 3: source + normalized job_url
            elif clean_job_url and clean_job_url in job_url_map:
                matched_job = job_url_map[clean_job_url]
            # Priority 4: hash signature
            elif fp in hash_map:
                matched_job = hash_map[fp]

            if matched_job:
                matched_job_ids.add(matched_job.id if hasattr(matched_job, 'id') else id(matched_job))
                matched_job.last_seen = now
                matched_job.last_verified = now
                matched_job.consecutive_missing_count = 0
                matched_job.status = "ACTIVE"
                matched_job.verification_status = "VERIFIED"

                if job.get("salary_range") and not matched_job.salary_range:
                    matched_job.salary_range = job["salary_range"]
                    matched_job.min_salary_lpa = job.get("min_salary_lpa")
                    matched_job.max_salary_lpa = job.get("max_salary_lpa")
                if job.get("external_apply_url") and not matched_job.external_apply_url:
                    matched_job.external_apply_url = job["external_apply_url"]

                updated_count += 1
            else:
                new_job = Job(
                    external_job_id=job.get("external_job_id"),
                    title=job.get("title", ""),
                    company=job.get("company", ""),
                    department=job.get("department"),
                    location=job.get("location", ""),
                    country=job.get("country", "India"),
                    remote_type=job.get("remote_type", "Hybrid"),
                    employment_type=job.get("employment_type", "Full-time"),
                    experience_level=job.get("experience_level", "Fresher"),
                    salary_range=job.get("salary_range"),
                    min_salary_lpa=job.get("min_salary_lpa"),
                    max_salary_lpa=job.get("max_salary_lpa"),
                    currency=job.get("currency", "INR"),
                    job_url=job.get("job_url", ""),
                    source_url=job.get("source_url") or job.get("job_url") or "",
                    external_apply_url=job.get("external_apply_url"),
                    apply_url=job.get("apply_url"),
                    canonical_url=job.get("canonical_url"),
                    source=job.get("source") or connector_name,
                    source_type=job.get("source_type", "ATS"),
                    raw_tags=job.get("raw_tags"),
                    skills=job.get("skills"),
                    benefits=job.get("benefits"),
                    description=job.get("description"),
                    hash_signature=fp,
                    status="ACTIVE",
                    verification_status="VERIFIED",
                    first_seen=now,
                    last_seen=now,
                    last_verified=now,
                    consecutive_missing_count=0
                )
                db.add(new_job)
                new_job_entities.append(new_job)
                inserted_count += 1

                # Update in-memory identity maps so subsequent batch items match this entity
                hash_map[fp] = new_job
                if ext_id and str(ext_id).strip():
                    ext_id_map[str(ext_id).strip()] = new_job
                if clean_canon:
                    canonical_map[clean_canon] = new_job
                if clean_job_url:
                    job_url_map[clean_job_url] = new_job

        removed_count = 0
        for j in existing_jobs:
            if j.status == "ACTIVE" and j.id not in matched_job_ids:
                j.consecutive_missing_count += 1
                if j.consecutive_missing_count >= threshold:
                    j.status = "REMOVED"
                    j.verification_status = "REMOVED_FROM_SOURCE"
                    removed_count += 1

        # Attempt flush to catch any DB uniqueness collisions safely
        try:
            await db.flush()
        except IntegrityError:
            await db.rollback()

            # Recovery: query existing DB jobs by hash signatures
            res_rec = await db.execute(select(Job).where(Job.hash_signature.in_(fps)))
            rec_map = {j.hash_signature: j for j in res_rec.scalars().all()}

            inserted_count = 0
            updated_count = 0
            new_job_entities = []
            matched_job_ids = set()

            for job in jobs_data:
                fp = job.get("hash_signature") or cls.generate_fingerprint(job)
                if fp in rec_map:
                    j = rec_map[fp]
                    matched_job_ids.add(j.id)
                    j.last_seen = now
                    j.last_verified = now
                    j.consecutive_missing_count = 0
                    j.status = "ACTIVE"
                    j.verification_status = "VERIFIED"
                    updated_count += 1
                else:
                    new_job = Job(
                        external_job_id=job.get("external_job_id"),
                        title=job.get("title", ""),
                        company=job.get("company", ""),
                        department=job.get("department"),
                        location=job.get("location", ""),
                        country=job.get("country", "India"),
                        remote_type=job.get("remote_type", "Hybrid"),
                        employment_type=job.get("employment_type", "Full-time"),
                        experience_level=job.get("experience_level", "Fresher"),
                        salary_range=job.get("salary_range"),
                        min_salary_lpa=job.get("min_salary_lpa"),
                        max_salary_lpa=job.get("max_salary_lpa"),
                        currency=job.get("currency", "INR"),
                        job_url=job.get("job_url", ""),
                        source_url=job.get("source_url") or job.get("job_url") or "",
                        external_apply_url=job.get("external_apply_url"),
                        apply_url=job.get("apply_url"),
                        canonical_url=job.get("canonical_url"),
                        source=job.get("source") or connector_name,
                        source_type=job.get("source_type", "ATS"),
                        raw_tags=job.get("raw_tags"),
                        skills=job.get("skills"),
                        benefits=job.get("benefits"),
                        description=job.get("description"),
                        hash_signature=fp,
                        status="ACTIVE",
                        verification_status="VERIFIED",
                        first_seen=now,
                        last_seen=now,
                        last_verified=now,
                        consecutive_missing_count=0
                    )
                    db.add(new_job)
                    rec_map[fp] = new_job
                    new_job_entities.append(new_job)
                    inserted_count += 1
            await db.flush()

        return inserted_count, updated_count, removed_count, new_job_entities

