import asyncio
import unittest
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from backend.app.database import Base, get_db
from backend.app.main import app


class TestManualJobPosting(unittest.TestCase):
    def setUp(self):
        self.engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
        self.TestingSessionLocal = sessionmaker(
            autocommit=False, autoflush=False, bind=self.engine, class_=AsyncSession
        )

        async def setup_db():
            async with self.engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)

        asyncio.run(setup_db())

        async def override_get_db():
            async with self.TestingSessionLocal() as session:
                yield session

        app.dependency_overrides[get_db] = override_get_db
        self.client = TestClient(app)

    def tearDown(self):
        app.dependency_overrides.clear()

    def test_create_manual_job_success(self):
        payload = {
            "title": "Senior Staff Python Backend Engineer",
            "company": "ScaleAI Robotics",
            "job_url": "https://scale.ai/careers/python-lead-101?utm_source=test",
            "location": "Bengaluru, India",
            "remote_type": "Remote",
            "experience_level": "Senior",
            "employment_type": "Full-time",
            "salary_range": "₹35 - ₹50 LPA",
            "min_salary_lpa": 35.0,
            "max_salary_lpa": 50.0,
            "tags": "Python, FastAPI, Docker, Kubernetes, Distributed Systems",
            "description": "Architect high-scale distributed backends."
        }

        res = self.client.post("/api/v1/jobs/manual", json=payload)
        self.assertEqual(res.status_code, 201)
        data = res.json()
        self.assertTrue(data["success"])
        job = data["data"]
        self.assertEqual(job["company"], "ScaleAI Robotics")
        self.assertEqual(job["title"], "Senior Staff Python Backend Engineer")
        self.assertEqual(job["source"], "Admin Manual")
        self.assertEqual(job["status"], "ACTIVE")
        self.assertEqual(job["verification_status"], "VERIFIED")
        self.assertEqual(job["salary_range"], "₹35 - ₹50 LPA")
        self.assertEqual(job["min_salary_lpa"], 35.0)
        self.assertIn("Python", job["tags"])
        # Ensure tracking params were stripped
        self.assertEqual(job["job_url"], "https://scale.ai/careers/python-lead-101")

    def test_manual_job_update_on_duplicate_url(self):
        payload1 = {
            "title": "Frontend Engineer",
            "company": "NextGen UI",
            "job_url": "https://nextgen.dev/jobs/fe-101",
            "experience_level": "Fresher"
        }
        res1 = self.client.post("/api/v1/jobs/manual", json=payload1)
        self.assertEqual(res1.status_code, 201)
        job1_id = res1.json()["data"]["id"]

        # Post again with updated title & salary
        payload2 = {
            "title": "Senior Frontend Engineer",
            "company": "NextGen UI",
            "job_url": "https://nextgen.dev/jobs/fe-101",
            "experience_level": "Senior",
            "salary_range": "₹20 - ₹25 LPA"
        }
        res2 = self.client.post("/api/v1/jobs/manual", json=payload2)
        self.assertEqual(res2.status_code, 201)
        job2 = res2.json()["data"]
        self.assertEqual(job2["id"], job1_id)
        self.assertEqual(job2["title"], "Senior Frontend Engineer")
        self.assertEqual(job2["salary_range"], "₹20 - ₹25 LPA")

    def test_manual_job_discovery_feed_and_search(self):
        payload = {
            "title": "Machine Learning Research Engineer",
            "company": "DeepNova Labs",
            "job_url": "https://deepnova.ai/jobs/ml-res",
            "location": "Hyderabad, India",
            "remote_type": "Hybrid",
            "experience_level": "Fresher",
            "tags": "PyTorch, Deep Learning, NLP"
        }
        create_res = self.client.post("/api/v1/jobs/manual", json=payload)
        self.assertEqual(create_res.status_code, 201)

        # 1. Test Discovery Feed (GET /jobs/search with empty keyword)
        feed_res = self.client.get("/api/v1/jobs/search")
        self.assertEqual(feed_res.status_code, 200)
        feed_data = feed_res.json()
        self.assertTrue(any(j["company"] == "DeepNova Labs" for j in feed_data["data"]))

        # 2. Test Keyword Search (GET /jobs/search?keyword=DeepNova)
        search_res = self.client.get("/api/v1/jobs/search?keyword=DeepNova")
        self.assertEqual(search_res.status_code, 200)
        search_data = search_res.json()
        self.assertTrue(any(j["company"] == "DeepNova Labs" for j in search_data["data"]))

        # 3. Test Direct Job List (GET /jobs)
        list_res = self.client.get("/api/v1/jobs?company=DeepNova")
        self.assertEqual(list_res.status_code, 200)
        list_data = list_res.json()
        self.assertEqual(len(list_data["data"]), 1)
        self.assertEqual(list_data["data"][0]["company"], "DeepNova Labs")

    def test_manual_job_deletion(self):
        payload = {
            "title": "DevOps Engineer",
            "company": "CloudTech Systems",
            "job_url": "https://cloudtech.io/jobs/devops-101"
        }
        create_res = self.client.post("/api/v1/jobs/manual", json=payload)
        self.assertEqual(create_res.status_code, 201)
        job_id = create_res.json()["data"]["id"]

        # Delete job
        del_res = self.client.delete(f"/api/v1/jobs/{job_id}")
        self.assertEqual(del_res.status_code, 200)
        self.assertTrue(del_res.json()["success"])

        # Verify it's no longer in active search
        feed_res = self.client.get("/api/v1/jobs/search")
        self.assertFalse(any(j["id"] == job_id for j in feed_res.json()["data"]))


if __name__ == "__main__":
    unittest.main()
