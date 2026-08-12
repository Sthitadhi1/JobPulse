import unittest
import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy import select

from backend.app.database import Base
from backend.app.models.job import DiscoveryLock, Job
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
