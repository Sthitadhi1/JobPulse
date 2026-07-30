import hashlib
import re
from typing import Dict, Any, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from backend.app.models.job import Job

class DeduplicatorEngine:
    @staticmethod
    def generate_fingerprint(company: str, title: str, location: str) -> str:
        clean_company = re.sub(r'[^a-z0-9]', '', company.lower())
        clean_title = re.sub(r'[^a-z0-9]', '', title.lower())
        clean_loc = re.sub(r'[^a-z0-9]', '', location.lower())

        raw_str = f"{clean_company}:{clean_title}:{clean_loc}"
        return hashlib.sha256(raw_str.encode('utf-8')).hexdigest()

    @classmethod
    async def filter_duplicates(cls, db: AsyncSession, jobs_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        if not jobs_data:
            return []

        prepared_jobs = []
        fingerprints = []
        for job in jobs_data:
            fp = cls.generate_fingerprint(job["company"], job["title"], job["location"])
            job["hash_signature"] = fp
            prepared_jobs.append(job)
            fingerprints.append(fp)

        result = await db.execute(select(Job.hash_signature).where(Job.hash_signature.in_(fingerprints)))
        existing_fps = set(result.scalars().all())

        unique_jobs = []
        seen_in_batch = set()

        for job in prepared_jobs:
            fp = job["hash_signature"]
            if fp not in existing_fps and fp not in seen_in_batch:
                unique_jobs.append(job)
                seen_in_batch.add(fp)

        return unique_jobs
