import datetime
from typing import List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from backend.app.connectors.registry import connector_registry
from backend.app.engine.normalizer import NormalizerEngine
from backend.app.engine.deduplicator import DeduplicatorEngine
from backend.app.engine.verification import VerificationEngine
from backend.app.engine.matching import MatchingEngine
from backend.app.models.job import Job, SavedSearch, NotificationLog

class SchedulerEngine:
    @classmethod
    def validate_job_data(cls, job: Dict[str, Any]) -> bool:
        """
        PART 13 — Input Validation:
        Title exists, Company exists, Job URL valid, Source valid, Location exists.
        """
        if not job.get("title") or not str(job.get("title")).strip():
            return False
        if not job.get("company") or not str(job.get("company")).strip():
            return False
        job_url = job.get("job_url") or job.get("apply_url")
        if not job_url or job_url == "#":
            return False
        if not job.get("source") or not str(job.get("source")).strip():
            return False
        if not job.get("location") or not str(job.get("location")).strip():
            return False
        return True

    @classmethod
    async def run_discovery_cycle(cls, db: AsyncSession) -> Dict[str, Any]:
        """
        Executes complete ingestion pipeline (PART 8):
        Discover Jobs -> Update Existing Jobs -> Insert New Jobs -> Verify Existing Jobs -> Check Missing Jobs -> Mark Removed
        """
        # Step 1: Fetch raw job postings from connectors
        raw_jobs = await connector_registry.run_all_connectors(db)

        # Step 2: Normalize fields
        normalized_jobs = [NormalizerEngine.normalize_job_data(j) for j in raw_jobs]

        # Step 3: Validate required fields
        valid_jobs = []
        skipped_jobs = 0
        for j in normalized_jobs:
            if cls.validate_job_data(j):
                valid_jobs.append(j)
            else:
                skipped_jobs += 1

        # Step 4: Process batch: update existing jobs and filter new unique jobs
        unique_jobs, updated_jobs_count = await DeduplicatorEngine.process_and_update_jobs(db, valid_jobs)

        # Step 5: Persist clean new jobs
        new_job_entities = []
        for j_data in unique_jobs:
            job_obj = Job(**j_data)
            db.add(job_obj)
            new_job_entities.append(job_obj)

        await db.commit()

        # Step 6: Refresh entities to get assigned IDs
        for job_obj in new_job_entities:
            await db.refresh(job_obj)

        # Step 7: Verify active jobs in database
        active_jobs_res = await db.execute(select(Job).where(Job.status == "ACTIVE").limit(100))
        active_jobs = active_jobs_res.scalars().all()
        verified_count, removed_count = await VerificationEngine.verify_jobs_batch(db, active_jobs)

        # Step 8: Load active saved searches and match new jobs
        res = await db.execute(select(SavedSearch).where(SavedSearch.is_active == True))
        active_searches = res.scalars().all()

        notifications_queued = 0
        for job_obj in new_job_entities:
            for search in active_searches:
                is_match, score, reasons = MatchingEngine.evaluate_job_against_search(job_obj, search)
                if is_match:
                    recipient = search.telegram_chat_id or "STUDENT_TELEGRAM_DEMO"
                    reason_text = " • " + "\n • ".join(reasons) if reasons else "Matched your search preferences."
                    
                    notif = NotificationLog(
                        user_id=search.user_id,
                        job_id=job_obj.id,
                        saved_search_id=search.id,
                        channel="Telegram",
                        recipient=recipient,
                        status="DELIVERED",
                        match_reason=reason_text
                    )
                    db.add(notif)
                    search.last_matched = datetime.datetime.utcnow()
                    notifications_queued += 1

        await db.commit()

        return {
            "status": "SUCCESS",
            "raw_jobs_found": len(raw_jobs),
            "valid_jobs": len(valid_jobs),
            "skipped_invalid_jobs": skipped_jobs,
            "jobs_updated": updated_jobs_count,
            "new_unique_jobs_added": len(unique_jobs),
            "jobs_verified": verified_count,
            "jobs_removed": removed_count,
            "notifications_dispatched": notifications_queued,
            "timestamp": datetime.datetime.utcnow().isoformat()
        }

scheduler_engine = SchedulerEngine()

