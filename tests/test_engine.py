import unittest
import asyncio
from backend.app.engine.normalizer import NormalizerEngine, URLNormalizerValidator
from backend.app.engine.dead_link import DeadLinkValidator
from backend.app.engine.deduplicator import DeduplicatorEngine
from backend.app.engine.search import SearchEngine
from backend.app.engine.matching import MatchingEngine
from backend.app.engine.scheduler import SchedulerEngine
from backend.app.notifications.telegram import TelegramNotificationService
from sqlalchemy.future import select
from backend.app.database import Base
from backend.app.models.job import Job, SavedSearch
from backend.app.models.search_request import SearchRequest
from backend.app.models.application import JobApplication

class TestJobPulseEngine(unittest.TestCase):
    def test_search_request_to_dict(self):
        req = SearchRequest(keyword="Machine Learning", location="Bangalore", min_salary_lpa=12.0, max_salary_lpa=18.0)
        d = req.to_dict()
        self.assertEqual(d["keyword"], "Machine Learning")
        self.assertEqual(d["location"], "Bangalore")
        self.assertEqual(d["min_salary_lpa"], 12.0)
        self.assertEqual(d["max_salary_lpa"], 18.0)

    def test_url_normalizer_strip_tracking_params(self):
        dirty_url = "https://in.linkedin.com/jobs/view/12345?utm_source=feed&refId=abc1234&trackingId=xyz"
        clean = URLNormalizerValidator.strip_tracking_params(dirty_url)
        self.assertEqual(clean, "https://in.linkedin.com/jobs/view/12345")

    def test_dead_link_validator_live_url(self):
        # Async test execution for DeadLinkValidator
        async def run_check():
            is_alive, status = await DeadLinkValidator.validate_url_alive("https://www.google.com")
            self.assertTrue(is_alive)
            self.assertIn(status, [200, 302])

            dead_alive, dead_status = await DeadLinkValidator.validate_url_alive("https://httpbin.org/status/404")
            self.assertFalse(dead_alive)

        asyncio.run(run_check())

    def test_normalizer_url_and_experience(self):
        raw_fresher = {
            "title": "Junior Backend Engineer (SDE 1)",
            "company": "Tech Corp",
            "location": "Bengaluru",
            "salary": "₹12 - ₹16 LPA",
            "job_url": "https://careers.techcorp.com/jobs/sde-1",
            "source_url": "https://careers.techcorp.com/jobs",
            "external_apply_url": "https://careers.techcorp.com/jobs/sde-1/apply",
            "description": "Building microservices with Python, FastAPI, Docker, and PostgreSQL."
        }
        normalized = NormalizerEngine.normalize_job_data(raw_fresher)
        self.assertIn(normalized["experience_level"], ["Fresher", "Associate", "Fresher / 0-1 YOE"])
        self.assertEqual(normalized["min_salary_lpa"], 12.0)
        self.assertEqual(normalized["max_salary_lpa"], 16.0)
        self.assertEqual(normalized["job_url"], "https://careers.techcorp.com/jobs/sde-1")
        self.assertEqual(normalized["source_url"], "https://careers.techcorp.com/jobs")
        self.assertEqual(normalized["external_apply_url"], "https://careers.techcorp.com/jobs/sde-1/apply")
        self.assertIn("Python", normalized["raw_tags"])

    def test_mid_level_guardrail_1_3_yoe(self):
        raw_mid = {
            "title": "Software Engineer",
            "company": "Growth Inc",
            "location": "Bengaluru",
            "description": "Requires 1-3 years of experience in Python and microservices."
        }
        normalized_mid = NormalizerEngine.normalize_job_data(raw_mid)
        self.assertEqual(normalized_mid["experience_level"], "Mid-Level")
        self.assertNotEqual(normalized_mid["experience_level"], "Fresher")

    def test_no_fabricated_salary_when_missing(self):
        raw_no_salary = {
            "title": "Software Engineer",
            "company": "Live Company",
            "location": "Bengaluru",
            "job_url": "https://company.com/jobs/123",
            "description": "Backend role."
        }
        normalized = NormalizerEngine.normalize_job_data(raw_no_salary)
        self.assertIsNone(normalized["salary_range"])
        self.assertIsNone(normalized["min_salary_lpa"])
        self.assertIsNone(normalized["max_salary_lpa"])

    def test_two_stage_url_validation(self):
        rel_url = "/careers/jobs/sde-backend-101"
        source_url = "https://swiggy.com/careers"
        resolved, valid, was_rel = URLNormalizerValidator.resolve_and_validate_url(rel_url, source_url)
        self.assertEqual(resolved, "https://swiggy.com/careers/jobs/sde-backend-101")
        self.assertTrue(valid)
        self.assertTrue(was_rel)

    def test_url_normalizer_department_rejection(self):
        dept_url = "https://phonepe.com/careers/job-openings/?department=data_science"
        _, valid_dept, _ = URLNormalizerValidator.resolve_and_validate_url(dept_url)
        self.assertFalse(valid_dept)

    def test_deduplicator_priority_fingerprint(self):
        job1 = {"external_job_id": "gh-101", "company": "Vercel", "title": "SDE", "location": "Remote"}
        job2 = {"external_job_id": "gh-101", "company": "Vercel", "title": "Software Engineer", "location": "India"}
        self.assertEqual(DeduplicatorEngine.generate_fingerprint(job1), DeduplicatorEngine.generate_fingerprint(job2))

    def test_job_validation(self):
        valid_job = {
            "title": "Software Engineer",
            "company": "Swiggy",
            "job_url": "https://boards.greenhouse.io/swiggy/jobs/123",
            "source": "Company Careers",
            "location": "Bengaluru"
        }
        invalid_job = {
            "title": "",
            "company": "Swiggy",
            "job_url": "#",
            "source": "Company Careers",
            "location": "Bengaluru"
        }
        self.assertTrue(SchedulerEngine.validate_job_data(valid_job))
        self.assertFalse(SchedulerEngine.validate_job_data(invalid_job))

    def test_telegram_formatting_and_escaping(self):
        job = {
            "company": "CRED & Co.",
            "title": "SDE 1 [Backend]",
            "location": "Bengaluru, India",
            "experience_level": "Fresher / 0-1 YOE",
            "salary_range": "₹15 - ₹20 LPA",
            "remote_type": "On-site",
            "job_url": "https://cred.club/careers/sde1"
        }
        msg = TelegramNotificationService.format_job_match_message(job, "• Match Reason")
        self.assertIn("CRED & Co\\.", msg)
        self.assertIn("\\[Backend\\]", msg)

    def test_boolean_search_conditions(self):
        cond = SearchEngine.build_boolean_conditions("Backend AND Python NOT Senior")
        self.assertIsNotNone(cond)

    def test_matching_engine_evaluation(self):
        job = Job(
            title="Software Development Engineer 1 (SDE I)",
            company="Razorpay",
            location="Bengaluru",
            remote_type="Hybrid",
            experience_level="Fresher / 0-1 YOE",
            min_salary_lpa=12.0,
            max_salary_lpa=16.0,
            raw_tags="Python, FastAPI, Docker",
            description="Backend engineer building payment microservices."
        )
        search = SavedSearch(
            name="Backend Fresh Grad",
            keywords="Software Engineer",
            location="Bengaluru",
            min_salary_lpa=10.0,
            experience_level="Fresher"
        )
        is_match, score, reasons = MatchingEngine.evaluate_job_against_search(job, search)
        self.assertTrue(is_match)
        self.assertGreater(score, 0)

    def test_job_application_model_creation(self):
        app = JobApplication(
            company="Swiggy",
            role="Backend Engineer",
            status="Applied"
        )
        self.assertEqual(app.company, "Swiggy")
        self.assertEqual(app.status, "Applied")

    def test_source_specific_reconciliation_and_freshness(self):
        async def run_check():
            from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
            engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
            AsyncSessionLocal = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)

            async with engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)

            async with AsyncSessionLocal() as session:
                # Cycle 1: Discovered job A from Source 1
                job_data_1 = [{
                    "external_job_id": "ext-101",
                    "title": "Backend Dev",
                    "company": "Company Alpha",
                    "location": "Bangalore",
                    "job_url": "https://alpha.com/jobs/101",
                    "source": "Source 1"
                }]

                ins, upd, rem, new_objs = await DeduplicatorEngine.reconcile_connector_jobs(
                    session, connector_name="Source 1", jobs_data=job_data_1
                )
                await session.commit()
                self.assertEqual(ins, 1)

                job_db = (await session.execute(select(Job).where(Job.external_job_id == "ext-101"))).scalars().first()
                self.assertEqual(job_db.status, "ACTIVE")
                self.assertEqual(job_db.consecutive_missing_count, 0)

                # Cycle 2: Source 1 returns empty set (job missing in cycle 1)
                ins, upd, rem, _ = await DeduplicatorEngine.reconcile_connector_jobs(
                    session, connector_name="Source 1", jobs_data=[]
                )
                await session.commit()
                self.assertEqual(job_db.consecutive_missing_count, 1)
                self.assertEqual(job_db.status, "ACTIVE")

                # Cycle 3: Source 1 returns empty set (job missing in cycle 2 -> threshold 2 reached)
                ins, upd, rem, _ = await DeduplicatorEngine.reconcile_connector_jobs(
                    session, connector_name="Source 1", jobs_data=[]
                )
                await session.commit()
                self.assertEqual(job_db.consecutive_missing_count, 2)
                self.assertEqual(job_db.status, "REMOVED")
                self.assertEqual(job_db.verification_status, "REMOVED_FROM_SOURCE")

                # Rediscovery: Job returns in Cycle 4
                ins, upd, rem, _ = await DeduplicatorEngine.reconcile_connector_jobs(
                    session, connector_name="Source 1", jobs_data=job_data_1
                )
                await session.commit()
                self.assertEqual(job_db.status, "ACTIVE")
                self.assertEqual(job_db.verification_status, "VERIFIED")
                self.assertEqual(job_db.consecutive_missing_count, 0)

            await engine.dispose()

        asyncio.run(run_check())

    def test_existing_job_identity_hierarchy_updates(self):
        async def run_check():
            from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
            engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
            AsyncSessionLocal = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)

            async with engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)

            async with AsyncSessionLocal() as session:
                # 1. ext_id match
                job1 = [{"external_job_id": "ext-999", "title": "Dev 1", "company": "Co", "source": "Src"}]
                ins, upd, _, _ = await DeduplicatorEngine.reconcile_connector_jobs(session, "Src", job1)
                await session.commit()
                self.assertEqual(ins, 1)

                job1_update = [{"external_job_id": "ext-999", "title": "Dev 1 Updated", "company": "Co", "source": "Src"}]
                ins, upd, _, _ = await DeduplicatorEngine.reconcile_connector_jobs(session, "Src", job1_update)
                await session.commit()
                self.assertEqual(upd, 1)

                # 2. canonical_url match
                job2 = [{"canonical_url": "https://co.com/job/2", "title": "Dev 2", "company": "Co", "source": "Src"}]
                ins, upd, _, _ = await DeduplicatorEngine.reconcile_connector_jobs(session, "Src", job2)
                await session.commit()
                self.assertEqual(ins, 1)

                job2_update = [{"canonical_url": "https://co.com/job/2", "title": "Dev 2 Updated", "company": "Co", "source": "Src"}]
                ins, upd, _, _ = await DeduplicatorEngine.reconcile_connector_jobs(session, "Src", job2_update)
                await session.commit()
                self.assertEqual(upd, 1)

                # 3. hash_signature match
                job3 = [{"title": "Dev 3", "company": "Co 3", "location": "Remote", "source": "Src"}]
                ins, upd, _, _ = await DeduplicatorEngine.reconcile_connector_jobs(session, "Src", job3)
                await session.commit()
                self.assertEqual(ins, 1)

                job3_update = [{"title": "Dev 3", "company": "Co 3", "location": "Remote", "source": "Src"}]
                ins, upd, _, _ = await DeduplicatorEngine.reconcile_connector_jobs(session, "Src", job3_update)
                await session.commit()
                self.assertEqual(upd, 1)

            await engine.dispose()

        asyncio.run(run_check())

    def test_duplicate_batch_and_integrity_error_recovery(self):
        async def run_check():
            from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
            engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
            AsyncSessionLocal = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)

            async with engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)

            async with AsyncSessionLocal() as session:
                # Same batch duplicate items
                duplicate_batch = [
                    {"external_job_id": "batch-1", "title": "SDE", "company": "TestCo", "source": "TestSource"},
                    {"external_job_id": "batch-1", "title": "SDE", "company": "TestCo", "source": "TestSource"}
                ]
                ins, upd, _, _ = await DeduplicatorEngine.reconcile_connector_jobs(session, "TestSource", duplicate_batch)
                await session.commit()
                self.assertEqual(ins, 1)
                self.assertEqual(upd, 1)

            await engine.dispose()

        asyncio.run(run_check())

    def test_active_dashboard_filtering_and_pagination(self):
        async def run_check():
            from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
            from backend.app.main import app
            from backend.app.database import get_db
            from fastapi.testclient import TestClient

            engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
            AsyncSessionLocal = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)

            async with engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)

            async with AsyncSessionLocal() as session:
                # 1. Insert 5 ACTIVE, 5 REMOVED, 5 EXPIRED jobs
                for i in range(5):
                    j_act = Job(
                        title=f"Software Engineer Active {i}",
                        company="Acme Corp",
                        location="Bangalore",
                        source="TestSource",
                        job_url=f"https://example.com/active-{i}",
                        source_url="https://example.com/source",
                        hash_signature=f"hash-active-{i}",
                        status="ACTIVE"
                    )
                    j_rem = Job(
                        title=f"Software Engineer Removed {i}",
                        company="Acme Corp",
                        location="Bangalore",
                        source="TestSource",
                        job_url=f"https://example.com/removed-{i}",
                        source_url="https://example.com/source",
                        hash_signature=f"hash-removed-{i}",
                        status="REMOVED"
                    )
                    j_exp = Job(
                        title=f"Software Engineer Expired {i}",
                        company="Acme Corp",
                        location="Bangalore",
                        source="TestSource",
                        job_url=f"https://example.com/expired-{i}",
                        source_url="https://example.com/source",
                        hash_signature=f"hash-expired-{i}",
                        status="EXPIRED"
                    )
                    session.add_all([j_act, j_rem, j_exp])
                await session.commit()

                # Override db dependency for TestClient
                async def override_get_db():
                    yield session

                app.dependency_overrides[get_db] = override_get_db
                client = TestClient(app)

                # Feed query check: only ACTIVE returned
                res = client.get("/api/v1/jobs")
                data = res.json()
                self.assertTrue(data["success"])
                self.assertEqual(data["meta"]["total_records"], 5)
                self.assertEqual(len(data["data"]), 5)
                for item in data["data"]:
                    self.assertEqual(item["status"], "ACTIVE")

                # Detail page check for non-active job
                res_detail = client.get("/api/v1/jobs/2")
                data_detail = res_detail.json()
                self.assertTrue(data_detail["success"])
                self.assertFalse(data_detail["data"]["is_active_opportunity"])
                self.assertEqual(data_detail["data"]["notice"], "This job is no longer active.")

                app.dependency_overrides.clear()

            await engine.dispose()

        asyncio.run(run_check())

    def test_pagination_and_bookmark_active_filtering(self):
        async def run_check():
            from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
            from backend.app.main import app
            from backend.app.database import get_db
            from fastapi.testclient import TestClient

            engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
            AsyncSessionLocal = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)

            async with engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)

            async with AsyncSessionLocal() as session:
                # 120 ACTIVE jobs, 80 REMOVED jobs
                active_jobs = [
                    Job(
                        title=f"Active Job {i}",
                        company="TechCorp",
                        location="Remote",
                        source="TestSource",
                        job_url=f"https://example.com/pg-act-{i}",
                        source_url="https://example.com/source",
                        hash_signature=f"hash-pg-act-{i}",
                        status="ACTIVE",
                        is_bookmarked=(i == 0)
                    )
                    for i in range(120)
                ]
                removed_jobs = [
                    Job(
                        title=f"Removed Job {i}",
                        company="TechCorp",
                        location="Remote",
                        source="TestSource",
                        job_url=f"https://example.com/pg-rem-{i}",
                        source_url="https://example.com/source",
                        hash_signature=f"hash-pg-rem-{i}",
                        status="REMOVED",
                        is_bookmarked=(i == 0)
                    )
                    for i in range(80)
                ]
                session.add_all(active_jobs + removed_jobs)
                await session.commit()

                async def override_get_db():
                    yield session

                app.dependency_overrides[get_db] = override_get_db
                client = TestClient(app)

                # Page 1 (limit 50)
                res_p1 = client.get("/api/v1/jobs?page=1&limit=50")
                d_p1 = res_p1.json()
                self.assertEqual(d_p1["meta"]["total_records"], 120)
                self.assertEqual(len(d_p1["data"]), 50)

                # Page 2 (limit 50)
                res_p2 = client.get("/api/v1/jobs?page=2&limit=50")
                d_p2 = res_p2.json()
                self.assertEqual(len(d_p2["data"]), 50)

                # Page 3 (limit 50)
                res_p3 = client.get("/api/v1/jobs?page=3&limit=50")
                d_p3 = res_p3.json()
                self.assertEqual(len(d_p3["data"]), 20)

                # Bookmarks filter check: returns only ACTIVE bookmarked job
                res_bm = client.get("/api/v1/jobs?bookmarked_only=true")
                d_bm = res_bm.json()
                self.assertEqual(d_bm["meta"]["total_records"], 1)
                self.assertEqual(d_bm["data"][0]["hash_signature"], "hash-pg-act-0")

                app.dependency_overrides.clear()

            await engine.dispose()

        asyncio.run(run_check())

if __name__ == "__main__":
    unittest.main()
