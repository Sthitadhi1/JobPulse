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
        2. Canonical URL
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
            raw_str = f"tier2:{clean_url}"
        elif clean_company and clean_title:
            raw_str = f"tier3:{clean_company}:{clean_title}"
        else:
            raw_str = f"tier4:{clean_company}:{clean_title}:{clean_loc}"

        return hashlib.sha256(raw_str.encode('utf-8')).hexdigest()

    @classmethod
    async def process_and_update_jobs(cls, db: AsyncSession, jobs_data: List[Dict[str, Any]]) -> Tuple[List[Dict[str, Any]], int]:
        """
        Deduplicates incoming batch, updates existing matching jobs in-place,
        and returns (new_unique_jobs_to_insert, count_of_updated_jobs).
        """
        if not jobs_data:
            return [], 0

        prepared_jobs = []
        fingerprints = []
        for job in jobs_data:
            fp = cls.generate_fingerprint(job)
            job["hash_signature"] = fp
            prepared_jobs.append(job)
            fingerprints.append(fp)

        # Query existing jobs matching fingerprints in chunks of 100 to avoid SQLite host parameter limits
        existing_jobs = {}
        chunk_size = 100
        for i in range(0, len(fingerprints), chunk_size):
            fp_chunk = fingerprints[i:i + chunk_size]
            result = await db.execute(select(Job).where(Job.hash_signature.in_(fp_chunk)))
            for j in result.scalars().all():
                existing_jobs[j.hash_signature] = j


        unique_jobs_to_insert = []
        seen_in_batch = set()
        updated_count = 0
        now = datetime.datetime.utcnow()

        for job_data in prepared_jobs:
            fp = job_data["hash_signature"]
            if fp in existing_jobs:
                # Update existing job in-place (PART 7 & 8)
                job_obj = existing_jobs[fp]
                job_obj.last_seen = now
                job_obj.last_verified = now
                job_obj.verification_count = (job_obj.verification_count or 1) + 1
                job_obj.status = "ACTIVE"
                job_obj.verification_status = "VERIFIED"
                job_obj.consecutive_missing_count = 0
                if job_data.get("external_apply_url"):
                    job_obj.external_apply_url = job_data.get("external_apply_url")
                updated_count += 1
            elif fp not in seen_in_batch:
                unique_jobs_to_insert.append(job_data)
                seen_in_batch.add(fp)

        if updated_count > 0:
            await db.commit()

        return unique_jobs_to_insert, updated_count

    @classmethod
    async def filter_duplicates(cls, db: AsyncSession, jobs_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        new_jobs, _ = await cls.process_and_update_jobs(db, jobs_data)
        return new_jobs

