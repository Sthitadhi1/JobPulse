import unittest
import asyncio
from backend.app.engine.normalizer import NormalizerEngine, URLNormalizerValidator
from backend.app.engine.deduplicator import DeduplicatorEngine
from backend.app.engine.search import SearchEngine
from backend.app.engine.matching import MatchingEngine
from backend.app.engine.scheduler import SchedulerEngine
from backend.app.engine.ai_layer import AIEngineLayer
from backend.app.connectors.ats import (
    GreenhouseATSConnector,
    LeverATSConnector,
    WorkdayATSConnector,
    AshbyATSConnector,
    GenericHTMLATSConnector
)
from backend.app.models.job import Job, SavedSearch

class TestJobPulseEngineV2(unittest.TestCase):
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
        # GUARDRAIL TEST: 1-3 YOE MUST NEVER BE CLASSIFIED AS FRESHER!
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
        # STEP 9 TEST: If salary is absent from official source, return None
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
        # 1. Relative URL Resolution to Absolute URL
        rel_url = "/careers/jobs/sde-backend-101"
        source_url = "https://swiggy.com/careers"
        resolved, valid, was_rel = URLNormalizerValidator.resolve_and_validate_url(rel_url, source_url)
        self.assertEqual(resolved, "https://swiggy.com/careers/jobs/sde-backend-101")
        self.assertTrue(valid)
        self.assertTrue(was_rel)

        # 2. Generic Career Homepage Rejection
        homepage_url = "https://company.com/careers"
        _, valid_hp, _ = URLNormalizerValidator.resolve_and_validate_url(homepage_url)
        self.assertFalse(valid_hp)

        # 3. Direct Individual Job Listing Validation
        direct_url = "https://boards.greenhouse.io/phonepe/jobs/7789865003"
        resolved_dir, valid_dir, _ = URLNormalizerValidator.resolve_and_validate_url(direct_url)
        self.assertEqual(resolved_dir, "https://boards.greenhouse.io/phonepe/jobs/7789865003")
        self.assertTrue(valid_dir)

    def test_url_normalizer_department_rejection(self):
        dept_url = "https://phonepe.com/careers/job-openings/?department=data_science"
        _, valid_dept, _ = URLNormalizerValidator.resolve_and_validate_url(dept_url)
        self.assertFalse(valid_dept)

        openings_url = "https://phonepe.com/careers/job-openings"
        _, valid_openings, _ = URLNormalizerValidator.resolve_and_validate_url(openings_url)
        self.assertFalse(valid_openings)

    def test_deduplicator_priority_fingerprint(self):
        job1 = {"external_job_id": "gh-101", "company": "Vercel", "title": "SDE", "location": "Remote"}
        job2 = {"external_job_id": "gh-101", "company": "Vercel", "title": "Software Engineer", "location": "India"}
        self.assertEqual(DeduplicatorEngine.generate_fingerprint(job1), DeduplicatorEngine.generate_fingerprint(job2))

        job3 = {"job_url": "https://jobs.lever.co/supabase/123", "company": "Supabase", "title": "SDE 1"}
        job4 = {"job_url": "https://jobs.lever.co/supabase/123/", "company": "Supabase Inc", "title": "Backend SDE"}
        self.assertEqual(DeduplicatorEngine.generate_fingerprint(job3), DeduplicatorEngine.generate_fingerprint(job4))

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

    def test_ats_connector_interfaces(self):
        gh = GreenhouseATSConnector()
        lever = LeverATSConnector()
        wd = WorkdayATSConnector()
        ashby = AshbyATSConnector()
        html = GenericHTMLATSConnector()

        self.assertEqual(gh.name, "Greenhouse")
        self.assertEqual(lever.name, "Lever")
        self.assertEqual(wd.name, "Workday")
        self.assertEqual(ashby.name, "Ashby")
        self.assertEqual(html.name, "Generic HTML")

    def test_ai_layer_natural_language_parsing(self):
        parsed = AIEngineLayer.parse_natural_language_query("Remote python backend fresher jobs in Bengaluru with 12 LPA")
        self.assertEqual(parsed["experience_level"], "Fresher")
        self.assertEqual(parsed["remote_type"], "Remote")
        self.assertEqual(parsed["min_salary"], 12.0)
        self.assertIn("python", parsed["keywords"])
        self.assertIn("backend", parsed["keywords"])

    def test_ai_layer_resume_matching(self):
        job = Job(
            id=101,
            title="Backend Software Engineer",
            company="Razorpay",
            raw_tags="Python, FastAPI, PostgreSQL, Docker, Redis",
            skills="Python, FastAPI, PostgreSQL"
        )
        resume = "Candidate with experience in Python, FastAPI, Docker, and SQL."
        analysis = AIEngineLayer.match_resume_to_job(resume, job)
        self.assertEqual(analysis["company"], "Razorpay")
        self.assertIn("Python", analysis["matched_skills"])
        self.assertIn("Fastapi", analysis["matched_skills"])

if __name__ == "__main__":
    unittest.main()
