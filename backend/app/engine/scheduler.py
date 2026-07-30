import datetime
from typing import List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from backend.app.connectors.registry import connector_registry
from backend.app.engine.normalizer import NormalizerEngine
from backend.app.engine.deduplicator import DeduplicatorEngine
from backend.app.engine.matching import MatchingEngine
from backend.app.models.job import Job, SavedSearch, NotificationLog

class SchedulerEngine:
    @classmethod
    async def run_discovery_cycle(cls, db: AsyncSession) -> Dict[str, Any]:
        """
        Executes complete ingestion pipeline:
        Fetch -> Normalize -> Validate -> Deduplicate -> Store -> Match -> Notify
        """
        # Step 1: Fetch raw job postings from connectors
        raw_jobs = await connector_registry.run_all_connectors(db)

        # Step 2: Normalize fields
        normalized_jobs = [NormalizerEngine.normalize_job_data(j) for j in raw_jobs]

        # Step 3: Deduplicate via SHA-256 fingerprinting
        unique_jobs = await DeduplicatorEngine.filter_duplicates(db, normalized_jobs)

        # Step 4: Persist clean non-duplicate jobs
        new_job_entities = []
        for j_data in unique_jobs:
            job_obj = Job(**j_data)
            db.add(job_obj)
            new_job_entities.append(job_obj)

        await db.commit()

        # Step 5: Refresh entities to get assigned IDs
        for job_obj in new_job_entities:
            await db.refresh(job_obj)

        # Step 6: Load active saved searches and match new jobs
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
            "new_unique_jobs_added": len(unique_jobs),
            "notifications_dispatched": notifications_queued,
            "timestamp": datetime.datetime.utcnow().isoformat()
        }

scheduler_engine = SchedulerEngine()
