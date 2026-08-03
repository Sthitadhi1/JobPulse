import datetime
import httpx
from typing import List, Dict, Any, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from backend.app.models.job import Job

class VerificationEngine:
    MISSING_THRESHOLD = 3 # Require 3 consecutive missing cycles before marking REMOVED / EXPIRED

    @classmethod
    async def verify_single_job(cls, client: httpx.AsyncClient, job: Job) -> str:
        """
        Step 7 & 10: Head request -> GET request -> 200 response -> Verification
        Returns new status: VERIFIED, REMOVED_FROM_SOURCE, or PENDING
        """
        target_url = job.external_apply_url or job.job_url
        if not target_url or target_url == "#":
            return "PENDING"

        try:
            resp = await client.head(target_url, timeout=5.0)
            if resp.status_code in [200, 301, 302]:
                return "VERIFIED"
            elif resp.status_code == 404:
                return "REMOVED_FROM_SOURCE"
            else:
                # GET fallback check
                get_resp = await client.get(target_url, timeout=5.0)
                if get_resp.status_code == 200:
                    return "VERIFIED"
                elif get_resp.status_code == 404:
                    return "REMOVED_FROM_SOURCE"
        except Exception:
            pass

        return "PENDING"

    @classmethod
    async def verify_jobs_batch(cls, db: AsyncSession, active_jobs: List[Job]) -> Tuple[int, int]:
        """
        Step 10: Persistent Standalone Verification Engine.
        Updates last_verified, verification_count, verification_status, status.
        Returns (verified_count, removed_count).
        """
        if not active_jobs:
            return 0, 0

        verified_count = 0
        removed_count = 0
        now = datetime.datetime.utcnow()

        async with httpx.AsyncClient(timeout=6.0, follow_redirects=True) as client:
            for job in active_jobs:
                v_res = await cls.verify_single_job(client, job)

                if v_res == "VERIFIED":
                    job.last_verified = now
                    job.verification_status = "VERIFIED"
                    job.verification_count = (job.verification_count or 1) + 1
                    job.consecutive_missing_count = 0
                    if job.status == "UNKNOWN":
                        job.status = "ACTIVE"
                    verified_count += 1
                elif v_res == "REMOVED_FROM_SOURCE":
                    job.consecutive_missing_count = (job.consecutive_missing_count or 0) + 1
                    job.verification_status = "REMOVED_FROM_SOURCE"
                    if job.consecutive_missing_count >= cls.MISSING_THRESHOLD:
                        job.status = "REMOVED"
                        removed_count += 1
                else:
                    # Connection error or timeout -> Do NOT remove! Mark UNKNOWN or PENDING
                    job.verification_status = "PENDING"

        await db.commit()
        return verified_count, removed_count

    @classmethod
    async def handle_missing_jobs(cls, db: AsyncSession, source_name: str, current_discovered_signatures: set) -> Tuple[int, int]:
        """
        Step 10: Missing jobs are verified multiple times before status transitions.
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
                job.consecutive_missing_count = (job.consecutive_missing_count or 0) + 1
                if job.consecutive_missing_count >= cls.MISSING_THRESHOLD:
                    job.status = "REMOVED"
                    job.verification_status = "REMOVED_FROM_SOURCE"
                    removed_count += 1
                else:
                    job.verification_status = "PENDING"

        await db.commit()
        return verified_count, removed_count
