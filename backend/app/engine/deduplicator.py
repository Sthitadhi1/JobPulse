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
