import unittest
import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy import select

from backend.app.database import Base
from backend.app.models.job import DiscoveryLock, Job, ConnectorExecution
from backend.app.engine.scheduler import SchedulerEngine

class TestScheduler(unittest.TestCase):
    def setUp(self):
        self.engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
        self.AsyncSessionLocal = async_sessionmaker(bind=self.engine, class_=AsyncSession, expire_on_commit=False)

    def tearDown(self):
        asyncio.run(self.engine.dispose())

    def test_discovery_lock_and_overlap_prevention(self):
        async def run_check():
            async with self.engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)

            async with self.AsyncSessionLocal() as session:
                # Pre-populate active lock
                lock = DiscoveryLock(
                    lock_name="discovery_cycle",
                    is_locked=True,
                    execution_id="active-lock-123",
                    locked_at=asyncio.run if False else None
                )
                import datetime
                lock.locked_at = datetime.datetime.utcnow()
                session.add(lock)
                await session.commit()

                # Attempt discovery cycle while locked
                res = await SchedulerEngine.run_discovery_cycle(session)
                self.assertEqual(res["status"], "ALREADY_RUNNING")
                self.assertEqual(res["execution_id"], "active-lock-123")

        asyncio.run(run_check())

    def test_stale_lock_recovery_and_interrupted_state(self):
        async def run_check():
            async with self.engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)

            async with self.AsyncSessionLocal() as session:
                import datetime
                old_time = datetime.datetime.utcnow() - datetime.timedelta(seconds=2000)

                stale_lock = DiscoveryLock(
                    lock_name="discovery_cycle",
                    is_locked=True,
                    execution_id="stale-exec-999",
                    locked_at=old_time
                )
                old_exec = ConnectorExecution(
                    execution_id="stale-exec-999",
                    connector_name="DiscoveryEngine",
                    source_type="Scheduler",
                    started_at=old_time,
                    finished_at=old_time,
                    duration_ms=0.0,
                    status="RUNNING"
                )
                session.add_all([stale_lock, old_exec])
                await session.commit()

                # Run discovery cycle with stale lock present
                res = await SchedulerEngine.run_discovery_cycle(session)
                self.assertEqual(res["status"], "SUCCESS")

                # Verify old execution became INTERRUPTED
                old_exec_refreshed = (await session.execute(
                    select(ConnectorExecution).where(ConnectorExecution.execution_id == "stale-exec-999")
                )).scalars().first()
                self.assertIsNotNone(old_exec_refreshed)
                self.assertEqual(old_exec_refreshed.status, "INTERRUPTED")
                self.assertIn("stale lock timeout", old_exec_refreshed.error_message)

        asyncio.run(run_check())

    def test_lock_release_ownership(self):
        async def run_check():
            async with self.engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)

            async with self.AsyncSessionLocal() as session:
                import datetime
                lock = DiscoveryLock(
                    lock_name="discovery_cycle",
                    is_locked=True,
                    execution_id="exec-AAA",
                    locked_at=datetime.datetime.utcnow()
                )
                session.add(lock)
                await session.commit()

                # Attempt releasing with wrong execution_id
                lock_res = await session.execute(select(DiscoveryLock).where(DiscoveryLock.lock_name == "discovery_cycle"))
                curr_lock = lock_res.scalars().first()
                if curr_lock and curr_lock.execution_id == "exec-BBB":
                    curr_lock.is_locked = False
                    await session.commit()

                # Lock should still belong to exec-AAA and remain locked
                refreshed_lock = (await session.execute(select(DiscoveryLock).where(DiscoveryLock.lock_name == "discovery_cycle"))).scalars().first()
                self.assertTrue(refreshed_lock.is_locked)
                self.assertEqual(refreshed_lock.execution_id, "exec-AAA")

        asyncio.run(run_check())

    def test_scheduler_validation(self):
        valid = {
            "title": "Software Engineer",
            "company": "Tech Corp",
            "job_url": "https://example.com/jobs/1",
            "source": "ATS",
            "location": "Remote"
        }
        invalid = {
            "title": "",
            "company": "Tech Corp",
            "job_url": "#",
            "source": "ATS",
            "location": "Remote"
        }
        self.assertTrue(SchedulerEngine.validate_job_data(valid))
        self.assertFalse(SchedulerEngine.validate_job_data(invalid))

if __name__ == "__main__":
    unittest.main()
