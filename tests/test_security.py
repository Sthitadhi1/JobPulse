import asyncio
import unittest
from unittest.mock import patch

from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from backend.app.config import settings
from backend.app.database import Base, get_db
from backend.app.main import app

ADMIN_EMAIL = "admin@jobpulse.test"
PASSWORD = "Password123"


class SecurityTestCase(unittest.TestCase):
    """Regression tests for access control on auth, admin, and per-user workspace endpoints."""

    def setUp(self):
        self.engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
        TestingSessionLocal = sessionmaker(
            autocommit=False, autoflush=False, bind=self.engine, class_=AsyncSession, expire_on_commit=False
        )

        async def setup_db():
            async with self.engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)

        asyncio.run(setup_db())

        async def override_get_db():
            async with TestingSessionLocal() as session:
                yield session

        app.dependency_overrides[get_db] = override_get_db
        self._orig = (settings.ADMIN_EMAILS, settings.SCHEDULER_SECRET)
        settings.ADMIN_EMAILS = ADMIN_EMAIL
        settings.SCHEDULER_SECRET = ""

    def tearDown(self):
        app.dependency_overrides.clear()
        settings.ADMIN_EMAILS, settings.SCHEDULER_SECRET = self._orig

    def client_for(self, email, name="Test User"):
        """Returns a TestClient signed in as a fresh account (session cookie kept by the client)."""
        client = TestClient(app)
        res = client.post("/api/v1/auth/signup", json={"name": name, "email": email, "password": PASSWORD})
        self.assertEqual(res.status_code, 201, res.text)
        return client


class TestPasswordReset(SecurityTestCase):
    def test_forgot_password_never_returns_code(self):
        self.client_for("alice@example.com")
        anon = TestClient(app)
        with patch("backend.app.api.auth.EmailService.send_otp_email") as send:
            res = anon.post("/api/v1/auth/forgot-password", json={"email": "alice@example.com"})
        self.assertEqual(res.status_code, 200)
        body = res.json()
        self.assertNotIn("otp_code", body)
        self.assertNotIn("reset_token", body)
        sent_code = send.call_args[0][1]
        self.assertNotIn(sent_code, res.text)

    def test_forgot_password_same_response_for_unknown_email(self):
        self.client_for("alice@example.com")
        anon = TestClient(app)
        with patch("backend.app.api.auth.EmailService.send_otp_email"):
            known = anon.post("/api/v1/auth/forgot-password", json={"email": "alice@example.com"}).json()
        unknown = anon.post("/api/v1/auth/forgot-password", json={"email": "nobody@example.com"}).json()
        self.assertEqual(known, unknown)

    def test_emailed_code_resets_password(self):
        self.client_for("alice@example.com")
        anon = TestClient(app)
        with patch("backend.app.api.auth.EmailService.send_otp_email") as send:
            anon.post("/api/v1/auth/forgot-password", json={"email": "alice@example.com"})
        code = send.call_args[0][1]
        res = anon.post("/api/v1/auth/reset-password-otp", json={
            "email": "alice@example.com", "otp": code, "new_password": "NewPassword456"
        })
        self.assertEqual(res.status_code, 200, res.text)
        login = TestClient(app).post("/api/v1/auth/login", json={"email": "alice@example.com", "password": "NewPassword456"})
        self.assertEqual(login.status_code, 200)

    def test_otp_locks_after_repeated_wrong_guesses(self):
        self.client_for("alice@example.com")
        anon = TestClient(app)
        with patch("backend.app.api.auth.EmailService.send_otp_email") as send:
            anon.post("/api/v1/auth/forgot-password", json={"email": "alice@example.com"})
        code = send.call_args[0][1]
        wrong = "000000" if code != "000000" else "111111"
        for _ in range(5):
            res = anon.post("/api/v1/auth/reset-password-otp", json={
                "email": "alice@example.com", "otp": wrong, "new_password": "Hacked123"
            })
            self.assertEqual(res.status_code, 400)
        # Even the correct code is refused once the attempt budget is spent.
        res = anon.post("/api/v1/auth/reset-password-otp", json={
            "email": "alice@example.com", "otp": code, "new_password": "Hacked123"
        })
        self.assertEqual(res.status_code, 429)


class TestAdminEndpoints(SecurityTestCase):
    JOB = {"title": "Backend Engineer", "company": "Acme Corp", "job_url": "https://acme.example/jobs/1"}

    def test_manual_job_post_requires_admin(self):
        self.assertEqual(TestClient(app).post("/api/v1/jobs/manual", json=self.JOB).status_code, 401)
        user = self.client_for("user@example.com")
        self.assertEqual(user.post("/api/v1/jobs/manual", json=self.JOB).status_code, 403)
        admin = self.client_for(ADMIN_EMAIL, name="Admin")
        self.assertEqual(admin.post("/api/v1/jobs/manual", json=self.JOB).status_code, 201)

    def test_job_unlisting_requires_admin(self):
        admin = self.client_for(ADMIN_EMAIL, name="Admin")
        job_id = admin.post("/api/v1/jobs/manual", json=self.JOB).json()["data"]["id"]
        self.assertEqual(TestClient(app).delete(f"/api/v1/jobs/{job_id}").status_code, 401)
        user = self.client_for("user@example.com")
        self.assertEqual(user.delete(f"/api/v1/jobs/{job_id}").status_code, 403)
        self.assertEqual(admin.delete(f"/api/v1/jobs/{job_id}").status_code, 200)

    def test_me_reports_admin_flag(self):
        self.assertFalse(self.client_for("user@example.com").get("/api/v1/auth/me").json()["user"]["is_admin"])
        self.assertTrue(self.client_for(ADMIN_EMAIL).get("/api/v1/auth/me").json()["user"]["is_admin"])

    def test_crawl_triggers_require_admin(self):
        anon = TestClient(app)
        for path in ["/api/v1/admin/connectors/sync", "/api/v1/admin/connectors/verify-dead-links",
                     "/api/v1/admin/connectors/dead-links/verify"]:
            self.assertEqual(anon.post(path).status_code, 401, path)

    def test_scheduler_endpoint_disabled_without_configured_secret(self):
        anon = TestClient(app)
        # The old hard-coded default must not grant access.
        res = anon.post("/api/v1/admin/connectors/run",
                        headers={"X-Scheduler-Secret": "jobpulse-internal-scheduler-secret"})
        self.assertEqual(res.status_code, 401)
        res = anon.post("/api/v1/admin/connectors/run", headers={"X-Scheduler-Secret": ""})
        self.assertEqual(res.status_code, 401)

    def test_scheduler_secret_grants_admin_access(self):
        settings.SCHEDULER_SECRET = "s3cret-for-tests"
        res = TestClient(app).post("/api/v1/admin/connectors/verify-dead-links",
                                   headers={"X-Scheduler-Secret": "s3cret-for-tests"})
        self.assertEqual(res.status_code, 200)


class TestWorkspaceIsolation(SecurityTestCase):
    def test_applications_require_login(self):
        anon = TestClient(app)
        self.assertEqual(anon.get("/api/v1/applications").status_code, 401)
        self.assertEqual(anon.post("/api/v1/applications", json={"company": "A", "role": "B"}).status_code, 401)
        self.assertEqual(anon.get("/api/v1/applications/export").status_code, 401)

    def test_applications_are_private_per_user(self):
        alice = self.client_for("alice@example.com")
        bob = self.client_for("bob@example.com")
        res = alice.post("/api/v1/applications", json={
            "company": "Stripe", "role": "SDE", "recruiter_email": "recruiter@stripe.example"
        })
        app_id = res.json()["id"]

        self.assertEqual(len(alice.get("/api/v1/applications").json()["data"]), 1)
        self.assertEqual(bob.get("/api/v1/applications").json()["data"], [])
        self.assertNotIn("Stripe", bob.get("/api/v1/applications/export").text)
        self.assertEqual(bob.patch(f"/api/v1/applications/{app_id}", json={"status": "Rejected"}).status_code, 403)
        self.assertEqual(bob.delete(f"/api/v1/applications/{app_id}").status_code, 403)

        self.assertEqual(alice.patch(f"/api/v1/applications/{app_id}", json={"status": "Interview"}).status_code, 200)
        self.assertEqual(alice.get("/api/v1/applications").json()["data"][0]["status"], "Interview")

    def test_saved_searches_are_private_per_user(self):
        alice = self.client_for("alice@example.com")
        bob = self.client_for("bob@example.com")
        self.assertEqual(TestClient(app).get("/api/v1/search/saved").status_code, 401)

        search_id = alice.post("/api/v1/search/saved", json={"name": "Python roles", "keywords": "python"}).json()["data"]["id"]
        self.assertEqual(bob.get("/api/v1/search/saved").json()["data"], [])
        self.assertEqual(bob.delete(f"/api/v1/search/saved/{search_id}").status_code, 403)
        self.assertEqual(bob.patch(f"/api/v1/search/saved/{search_id}/toggle").status_code, 403)
        self.assertEqual(len(alice.get("/api/v1/search/saved").json()["data"]), 1)

    def test_notification_endpoints_require_login(self):
        anon = TestClient(app)
        self.assertEqual(anon.get("/api/v1/notifications/logs").status_code, 401)
        self.assertEqual(anon.post("/api/v1/notifications/telegram/test", json={"chat_id": "1"}).status_code, 401)

    def test_bookmarks_require_login(self):
        admin = self.client_for(ADMIN_EMAIL, name="Admin")
        job_id = admin.post("/api/v1/jobs/manual", json=TestAdminEndpoints.JOB).json()["data"]["id"]
        self.assertEqual(TestClient(app).post(f"/api/v1/jobs/{job_id}/bookmark").status_code, 401)
        res = self.client_for("alice@example.com").post(f"/api/v1/jobs/{job_id}/bookmark")
        self.assertEqual(res.status_code, 200)
        self.assertTrue(res.json()["data"]["is_bookmarked"])


class TestPerUserBookmarksAndDashboard(SecurityTestCase):
    """Bookmarks, stars and dashboard counts belong to the signed-in user only."""

    def setUp(self):
        super().setUp()
        admin = self.client_for(ADMIN_EMAIL, name="Admin")
        self.job_a = admin.post("/api/v1/jobs/manual", json=TestAdminEndpoints.JOB).json()["data"]["id"]
        self.job_b = admin.post("/api/v1/jobs/manual", json={
            "title": "Frontend Engineer", "company": "Beta Labs", "job_url": "https://beta.example/jobs/2"
        }).json()["data"]["id"]
        self.alice = self.client_for("alice@example.com", name="Alice Smith")
        self.bob = self.client_for("bob@example.com", name="Bob Jones")
        self.anon = TestClient(app)

    @staticmethod
    def starred(client, path, **params):
        return {j["id"] for j in client.get(path, params=params).json()["data"] if j["is_bookmarked"]}

    def test_new_endpoints_require_login(self):
        self.assertEqual(self.anon.get("/api/v1/jobs/bookmarks").status_code, 401)
        self.assertEqual(self.anon.get("/api/v1/dashboard/overview").status_code, 401)

    def test_bookmarks_list_is_per_user(self):
        self.assertEqual(self.alice.get("/api/v1/jobs/bookmarks").json()["data"], [])
        res = self.alice.post(f"/api/v1/jobs/{self.job_a}/bookmark")
        self.assertTrue(res.json()["data"]["is_bookmarked"])

        alice_bms = self.alice.get("/api/v1/jobs/bookmarks").json()["data"]
        self.assertEqual([j["id"] for j in alice_bms], [self.job_a])
        self.assertTrue(alice_bms[0]["is_bookmarked"])
        self.assertEqual(self.bob.get("/api/v1/jobs/bookmarks").json()["data"], [])

        # Toggling again removes it.
        self.assertFalse(self.alice.post(f"/api/v1/jobs/{self.job_a}/bookmark").json()["data"]["is_bookmarked"])
        self.assertEqual(self.alice.get("/api/v1/jobs/bookmarks").json()["data"], [])

    def test_stars_in_feeds_are_per_user(self):
        self.alice.post(f"/api/v1/jobs/{self.job_a}/bookmark")
        self.bob.post(f"/api/v1/jobs/{self.job_b}/bookmark")

        for path in ["/api/v1/jobs", "/api/v1/jobs/search"]:
            self.assertEqual(self.starred(self.alice, path), {self.job_a}, path)
            self.assertEqual(self.starred(self.bob, path), {self.job_b}, path)
            self.assertEqual(self.starred(self.anon, path), set(), path)

        detail = f"/api/v1/jobs/{self.job_a}"
        self.assertTrue(self.alice.get(detail).json()["data"]["is_bookmarked"])
        self.assertFalse(self.bob.get(detail).json()["data"]["is_bookmarked"])
        self.assertFalse(self.anon.get(detail).json()["data"]["is_bookmarked"])

    def test_bookmarked_only_filter_is_per_user(self):
        self.alice.post(f"/api/v1/jobs/{self.job_a}/bookmark")
        ids = lambda c: [j["id"] for j in c.get("/api/v1/jobs", params={"bookmarked_only": True}).json()["data"]]
        self.assertEqual(ids(self.alice), [self.job_a])
        self.assertEqual(ids(self.bob), [])
        self.assertEqual(ids(self.anon), [])

    def test_dashboard_counts_are_per_user(self):
        self.alice.post(f"/api/v1/jobs/{self.job_a}/bookmark")
        self.alice.post(f"/api/v1/jobs/{self.job_b}/bookmark")
        self.alice.post("/api/v1/applications", json={"company": "Stripe", "role": "SDE", "status": "Applied"})
        self.alice.post("/api/v1/applications", json={"company": "Acme", "role": "SDE", "status": "Interview"})
        self.bob.post("/api/v1/applications", json={"company": "Beta", "role": "SDE", "status": "Offer"})

        alice = self.alice.get("/api/v1/dashboard/overview").json()
        self.assertEqual(alice["user_name"], "Alice Smith")
        self.assertEqual(alice["overview"]["bookmarked_jobs"], 2)
        self.assertEqual(alice["overview"]["applications"], 2)
        self.assertEqual(alice["pipeline"], {"saved": 0, "applied": 1, "oa_test": 0, "interview": 1, "offer": 0})

        bob = self.bob.get("/api/v1/dashboard/overview").json()
        self.assertEqual(bob["user_name"], "Bob Jones")
        self.assertEqual(bob["overview"]["bookmarked_jobs"], 0)
        self.assertEqual(bob["overview"]["applications"], 1)
        self.assertEqual(bob["pipeline"], {"saved": 0, "applied": 0, "oa_test": 0, "interview": 0, "offer": 1})


class TestPublicJobDiscovery(SecurityTestCase):
    """Anonymous visitors can browse jobs; only personal features need an account."""

    def test_job_browsing_is_public(self):
        admin = self.client_for(ADMIN_EMAIL, name="Admin")
        job_id = admin.post("/api/v1/jobs/manual", json=TestAdminEndpoints.JOB).json()["data"]["id"]
        anon = TestClient(app)
        self.assertEqual(anon.get("/api/v1/jobs").status_code, 200)
        self.assertEqual(anon.get(f"/api/v1/jobs/{job_id}").status_code, 200)
        self.assertEqual(anon.get("/api/v1/analytics/dashboard").status_code, 200)

    def test_robots_txt_allows_crawling(self):
        res = TestClient(app).get("/robots.txt")
        self.assertEqual(res.status_code, 200)
        self.assertIn("Allow: /", res.text)


if __name__ == "__main__":
    unittest.main()
