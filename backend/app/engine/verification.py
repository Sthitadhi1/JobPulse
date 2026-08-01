import datetime
import httpx
from typing import List, Dict, Any, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from backend.app.models.job import Job, ConnectorHealth, ConnectorExecution

class VerificationEngine:
    MISSING_THRESHOLD = 3 # Require 3 consecutive missing cycles before marking REMOVED

    @classmethod
    async def verify_jobs_batch(cls, db: AsyncSession, active_jobs: List[Job]) -> Tuple[int, int]:
        """
        Performs verification checks for active jobs in DB.
        Updates last_verified, verification_count, verification_status.
        Returns (verified_count, removed_count).
        """
        if not active_jobs:
            return 0, 0

        verified_count = 0
        removed_count = 0
        now = datetime.datetime.utcnow()

        async with httpx.AsyncClient(timeout=5.0, follow_redirects=True) as client:
            for job in active_jobs:
                target_url = job.external_apply_url or job.job_url
                if not target_url or target_url == "#":
                    job.verification_status = "PENDING"
                    continue

                try:
                    # Light HEAD / GET check for availability
                    resp = await client.head(target_url)
                    if resp.status_code in [200, 301, 302]:
                        job.last_verified = now
                        job.verification_status = "VERIFIED"
                        job.verification_count = (job.verification_count or 1) + 1
                        job.consecutive_missing_count = 0
                        verified_count += 1
                    elif resp.status_code == 404:
                        job.consecutive_missing_count = (job.consecutive_missing_count or 0) + 1
                        job.verification_status = "REMOVED_FROM_SOURCE"
                        if job.consecutive_missing_count >= cls.MISSING_THRESHOLD:
                            job.status = "REMOVED"
                            removed_count += 1
                    else:
                        job.verification_status = "PENDING"
                except Exception:
                    # Network timeout / temporary connection error -> NEVER remove job!
                    job.verification_status = "PENDING"

        await db.commit()
        return verified_count, removed_count

    @classmethod
    async def handle_missing_jobs(cls, db: AsyncSession, source_name: str, current_discovered_signatures: set) -> Tuple[int, int]:
        """
        Compares currently discovered job signatures against active jobs stored for source_name.
        Increments missing count for un-discovered jobs and transitions to REMOVED only after threshold.
        Returns (verified_count, removed_count).
        """
        result = await db.execute(
            select(Job).where(Job.source == source_name, Job.status == "ACTIVE")
        )
        stored_active_jobs = result.scalars().all()
        
        verified_count = 0
        removed_count = 0
        now = datetime.datetime.utcnow()

        for job in stored_active_jobs:
            if job.hash_signature in current_discovered_signatures:
                job.last_seen = now
                job.last_verified = now
                job.verification_status = "VERIFIED"
                job.consecutive_missing_count = 0
                verified_count += 1
            else:
                # Job not found in current crawl cycle
                job.consecutive_missing_count = (job.consecutive_missing_count or 0) + 1
                if job.consecutive_missing_count >= cls.MISSING_THRESHOLD:
                    job.status = "REMOVED"
                    job.verification_status = "REMOVED_FROM_SOURCE"
                    removed_count += 1
                else:
                    job.verification_status = "PENDING"

        await db.commit()
        return verified_count, removed_count
