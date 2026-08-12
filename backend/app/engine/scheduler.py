import time
import uuid
import datetime
from typing import List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from backend.app.connectors.registry import connector_registry
from backend.app.engine.normalizer import NormalizerEngine
from backend.app.engine.deduplicator import DeduplicatorEngine
from backend.app.engine.verification import VerificationEngine
from backend.app.engine.matching import MatchingEngine
from backend.app.models.job import Job, SavedSearch, NotificationLog, DiscoveryLock

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
        Executes complete ingestion pipeline with Discovery Lock and Telemetry:
        1. Acquire DB lock (prevent overlapping cycles)
        2. Generate unique execution_id
        3. Discover Jobs concurrently -> Normalize -> Validate -> Deduplicate -> Persist -> Verify -> Match Searches
        4. Release DB lock in finally block
        """
        execution_id = str(uuid.uuid4())
        t0 = time.time()
        now = datetime.datetime.utcnow()

        # Step 0: Acquire Discovery Lock
        lock_res = await db.execute(select(DiscoveryLock).where(DiscoveryLock.lock_name == "discovery_cycle"))
        lock = lock_res.scalars().first()

        if not lock:
            lock = DiscoveryLock(
                lock_name="discovery_cycle",
                is_locked=True,
                execution_id=execution_id,
                locked_at=now
            )
            db.add(lock)
            await db.commit()
        else:
            # Check for active lock (stale lock threshold = 60 minutes)
            if lock.is_locked and lock.locked_at and (now - lock.locked_at).total_seconds() < 3600:
                print(f"[DISCOVERY] ALREADY_RUNNING existing_execution_id={lock.execution_id} requested_execution_id={execution_id}")
                return {
                    "status": "ALREADY_RUNNING",
                    "message": "A discovery cycle is already executing.",
                    "execution_id": lock.execution_id,
                    "timestamp": now.isoformat()
                }
            # Take over lock
            lock.is_locked = True
            lock.execution_id = execution_id
            lock.locked_at = now
            await db.commit()

        print(f"[DISCOVERY] START execution_id={execution_id}")

        try:
            # Step 1: Fetch raw job postings from connectors concurrently
            raw_jobs = await connector_registry.run_all_connectors(db=db, execution_id=execution_id)

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

            duration_ms = round((time.time() - t0) * 1000.0, 2)
            print(f"[DISCOVERY] COMPLETE execution_id={execution_id} duration_ms={duration_ms}")

            return {
                "status": "SUCCESS",
                "execution_id": execution_id,
                "duration_ms": duration_ms,
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

        except Exception as e:
            duration_ms = round((time.time() - t0) * 1000.0, 2)
            print(f"[DISCOVERY] FAILED execution_id={execution_id} duration_ms={duration_ms} error={e}")
            raise e

        finally:
            # Always release Discovery Lock
            try:
                lock_res = await db.execute(select(DiscoveryLock).where(DiscoveryLock.lock_name == "discovery_cycle"))
                current_lock = lock_res.scalars().first()
                if current_lock and current_lock.execution_id == execution_id:
                    current_lock.is_locked = False
                    current_lock.execution_id = None
                    current_lock.locked_at = None
                    await db.commit()
            except Exception as le:
                print(f"[DISCOVERY] LOCK RELEASE ERROR: {le}")

scheduler_engine = SchedulerEngine()


