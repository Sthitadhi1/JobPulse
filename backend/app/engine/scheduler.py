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
from backend.app.config import settings
from backend.app.models.job import Job, SavedSearch, NotificationLog, DiscoveryLock, ConnectorExecution

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
        Executes complete discovery cycle with safe lock acquisition, stale lock recovery,
        and execution telemetry tracking.
        """
        execution_id = str(uuid.uuid4())
        t0 = time.time()
        now = datetime.datetime.utcnow()
        lock_timeout = getattr(settings, "DISCOVERY_LOCK_TIMEOUT_SECONDS", 900)

        # Step 0: Discovery Lock Management & Stale Recovery
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
            if lock.is_locked:
                lock_age = (now - lock.locked_at).total_seconds() if lock.locked_at else 0
                if lock_age < lock_timeout:
                    print(f"[DISCOVERY] ALREADY_RUNNING existing_execution_id={lock.execution_id} requested_execution_id={execution_id}")
                    return {
                        "status": "ALREADY_RUNNING",
                        "message": "A discovery cycle is already executing.",
                        "execution_id": lock.execution_id,
                        "timestamp": now.isoformat()
                    }

                # Stale lock recovery: Mark previous execution INTERRUPTED
                old_exec_id = lock.execution_id
                if old_exec_id:
                    exec_res = await db.execute(select(ConnectorExecution).where(ConnectorExecution.execution_id == old_exec_id))
                    old_executions = exec_res.scalars().all()
                    for old_exec in old_executions:
                        if old_exec.status in ["STARTING", "RUNNING"]:
                            old_exec.status = "INTERRUPTED"
                            old_exec.error_message = f"Interrupted due to stale lock timeout ({int(lock_age)}s >= {lock_timeout}s)"
                            old_exec.finished_at = now

                print(f"[DISCOVERY] STALE_LOCK_RECOVERED old_execution_id={old_exec_id} new_execution_id={execution_id} lock_age_seconds={int(lock_age)}")
                lock.is_locked = True
                lock.execution_id = execution_id
                lock.locked_at = now
                await db.commit()
            else:
                lock.is_locked = True
                lock.execution_id = execution_id
                lock.locked_at = now
                await db.commit()

        print(f"[DISCOVERY] START execution_id={execution_id}")

        # Create discovery execution telemetry summary record
        discovery_telemetry = ConnectorExecution(
            execution_id=execution_id,
            connector_name="DiscoveryEngine",
            source_type="Scheduler",
            started_at=now,
            finished_at=now,
            duration_ms=0.0,
            status="RUNNING"
        )
        db.add(discovery_telemetry)
        await db.commit()

        try:
            # Step 1: Run all connectors concurrently and reconcile source-specifically
            connector_results = await connector_registry.run_all_connectors(db=db, execution_id=execution_id)

            # Step 2: Aggregate metrics across connector runs
            jobs_discovered = sum(r.get("jobs_discovered", 0) for r in connector_results)
            jobs_inserted = sum(r.get("jobs_inserted", 0) for r in connector_results)
            jobs_updated = sum(r.get("jobs_updated", 0) for r in connector_results)
            jobs_removed = sum(r.get("jobs_removed", 0) for r in connector_results)
            connectors_successful = sum(1 for r in connector_results if r.get("status") == "SUCCESS")
            connectors_failed = sum(1 for r in connector_results if r.get("status") != "SUCCESS")

            # Collect newly created jobs for Telegram notification matching
            new_job_entities = []
            for r in connector_results:
                if r.get("status") == "SUCCESS":
                    new_job_entities.extend(r.get("new_job_entities", []))

            # Step 3: Verify active jobs batch (VerificationEngine dead link check)
            active_jobs_res = await db.execute(select(Job).where(Job.status == "ACTIVE").limit(100))
            active_jobs = active_jobs_res.scalars().all()
            verified_count, verify_removed_count = await VerificationEngine.verify_jobs_batch(db, active_jobs)
            total_removed = jobs_removed + verify_removed_count

            # Step 4: Load active saved searches and match new jobs
            res = await db.execute(select(SavedSearch).where(SavedSearch.is_active == True))
            active_searches = res.scalars().all()

            notifications_queued = 0
            for job_obj in new_job_entities:
                if getattr(job_obj, "status", "ACTIVE") != "ACTIVE":
                    continue
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
            discovery_telemetry.status = "COMPLETED"
            discovery_telemetry.finished_at = datetime.datetime.utcnow()
            discovery_telemetry.duration_ms = duration_ms
            discovery_telemetry.jobs_discovered = jobs_discovered
            discovery_telemetry.jobs_inserted = jobs_inserted
            discovery_telemetry.jobs_updated = jobs_updated
            discovery_telemetry.jobs_removed = total_removed
            discovery_telemetry.jobs_verified = verified_count
            await db.commit()

            print(f"[DISCOVERY] COMPLETE execution_id={execution_id} duration_ms={duration_ms}")

            return {
                "status": "SUCCESS",
                "execution_id": execution_id,
                "duration_ms": duration_ms,
                "jobs_discovered": jobs_discovered,
                "jobs_inserted": jobs_inserted,
                "jobs_updated": jobs_updated,
                "jobs_removed": total_removed,
                "connectors_successful": connectors_successful,
                "connectors_failed": connectors_failed,
                "notifications_dispatched": notifications_queued,
                "timestamp": datetime.datetime.utcnow().isoformat()
            }

        except Exception as e:
            duration_ms = round((time.time() - t0) * 1000.0, 2)
            discovery_telemetry.status = "FAILED"
            discovery_telemetry.error_message = str(e)
            discovery_telemetry.finished_at = datetime.datetime.utcnow()
            discovery_telemetry.duration_ms = duration_ms
            try:
                await db.commit()
            except Exception:
                pass
            print(f"[DISCOVERY] FAILED execution_id={execution_id} duration_ms={duration_ms} error={e}")
            raise e

        finally:
            # Release Discovery Lock only if held by current execution
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


