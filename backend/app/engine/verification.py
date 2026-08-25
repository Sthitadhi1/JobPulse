import asyncio
import datetime
from typing import List, Tuple
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.models.job import Job
from backend.app.engine.dead_link import DeadLinkValidator

class VerificationEngine:
    @classmethod
    async def verify_single_job(cls, job: Job) -> str:
        """
        Executes async dead-link check using DeadLinkValidator with soft-404 inspection.
        Returns: VERIFIED, REMOVED_FROM_SOURCE, or PENDING
        """
        target_url = job.external_apply_url or job.job_url
        if not target_url or target_url == "#":
            return "REMOVED_FROM_SOURCE"

        is_alive, status_code = await DeadLinkValidator.validate_url_alive(target_url, timeout_seconds=3.0)
        if is_alive:
            return "VERIFIED"
        elif status_code in [404, 410, 500, 502, 503]:
            return "REMOVED_FROM_SOURCE"
        else:
            return "PENDING"

    @classmethod
    async def verify_jobs_batch(cls, db: AsyncSession, active_jobs: List[Job], concurrency: int = 25) -> Tuple[int, int]:
        """
        Runs dead-link verification concurrently across active_jobs.
        Immediately updates DB and removes 404/410/dead listings.
        """
        if not active_jobs:
            return 0, 0

        verified_count = 0
        removed_count = 0
        now = datetime.datetime.utcnow()
        sem = asyncio.Semaphore(concurrency)

        async def verify_item(job: Job):
            async with sem:
                v_res = await cls.verify_single_job(job)
                return job, v_res

        results = await asyncio.gather(*[verify_item(j) for j in active_jobs], return_exceptions=True)

        for res in results:
            if isinstance(res, tuple):
                job, v_res = res
                if v_res == "VERIFIED":
                    job.last_verified = now
                    job.verification_status = "VERIFIED"
                    job.verification_count = (job.verification_count or 1) + 1
                    job.consecutive_missing_count = 0
                    if job.status == "UNKNOWN":
                        job.status = "ACTIVE"
                    verified_count += 1
                elif v_res == "REMOVED_FROM_SOURCE":
                    job.last_verified = now
                    job.verification_status = "REMOVED_FROM_SOURCE"
                    job.status = "REMOVED"
                    job.closed_at = now
                    job.closure_reason = "Link is no longer accessible on source portal (404/dead/closed)"
                    removed_count += 1
                else:
                    job.verification_status = "PENDING"

        await db.commit()
        return verified_count, removed_count
