import unittest
import asyncio
from backend.app.engine.normalizer import NormalizerEngine, URLNormalizerValidator
from backend.app.engine.dead_link import DeadLinkValidator
from backend.app.engine.deduplicator import DeduplicatorEngine
from backend.app.engine.search import SearchEngine
from backend.app.engine.matching import MatchingEngine
from backend.app.engine.scheduler import SchedulerEngine
from backend.app.notifications.telegram import TelegramNotificationService
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

if __name__ == "__main__":
    unittest.main()
