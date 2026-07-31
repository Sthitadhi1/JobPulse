import unittest
from backend.app.engine.normalizer import NormalizerEngine, URLNormalizerValidator
from backend.app.engine.deduplicator import DeduplicatorEngine
from backend.app.engine.search import SearchEngine
from backend.app.engine.matching import MatchingEngine
from backend.app.engine.scheduler import SchedulerEngine
from backend.app.notifications.telegram import TelegramNotificationService
from backend.app.models.job import Job, SavedSearch

class TestJobPulseEngine(unittest.TestCase):
    def test_normalizer_url_and_experience(self):
        raw = {
            "title": "Junior Backend Engineer (SDE 1)",
            "company": "Tech Corp",
            "location": "Bengaluru",
            "salary": "₹12 - ₹16 LPA",
            "job_url": "https://careers.techcorp.com/jobs/sde-1",
            "source_url": "https://careers.techcorp.com/jobs",
            "external_apply_url": "https://careers.techcorp.com/jobs/sde-1/apply",
            "description": "Building microservices with Python, FastAPI, Docker, and PostgreSQL."
        }
        normalized = NormalizerEngine.normalize_job_data(raw)
        self.assertEqual(normalized["experience_level"], "Fresher / 0-1 YOE")
        self.assertEqual(normalized["min_salary_lpa"], 12.0)
        self.assertEqual(normalized["max_salary_lpa"], 16.0)
        self.assertEqual(normalized["job_url"], "https://careers.techcorp.com/jobs/sde-1")
        self.assertEqual(normalized["source_url"], "https://careers.techcorp.com/jobs")
        self.assertEqual(normalized["external_apply_url"], "https://careers.techcorp.com/jobs/sde-1/apply")
        self.assertIn("Python", normalized["raw_tags"])

    def test_url_normalizer_validator_resolution(self):
        # 1. Relative URL Resolution to Absolute URL
        rel_url = "/careers/jobs/sde-backend-101"
        source_url = "https://swiggy.com/careers"
        resolved, valid, was_rel = URLNormalizerValidator.resolve_and_validate_url(rel_url, source_url)
        self.assertEqual(resolved, "https://swiggy.com/careers/jobs/sde-backend-101")
        self.assertTrue(valid)
        self.assertTrue(was_rel)

        # 2. Generic Career Homepage Rejection
        homepage_url = "https://company.com/careers"
        resolved_hp, valid_hp, _ = URLNormalizerValidator.resolve_and_validate_url(homepage_url)
        self.assertFalse(valid_hp)

        # 3. Direct Individual Job Listing Validation
        direct_url = "https://razorpay.com/jobs/sde-1-backend-301"
        resolved_dir, valid_dir, _ = URLNormalizerValidator.resolve_and_validate_url(direct_url)
        self.assertEqual(resolved_dir, "https://razorpay.com/jobs/sde-1-backend-301")
        self.assertTrue(valid_dir)

    def test_deduplicator_priority_fingerprint(self):
        # 1. Same external_job_id produces same hash
        job1 = {"external_job_id": "gh-101", "company": "Vercel", "title": "SDE", "location": "Remote"}
        job2 = {"external_job_id": "gh-101", "company": "Vercel", "title": "Software Engineer", "location": "India"}
        self.assertEqual(DeduplicatorEngine.generate_fingerprint(job1), DeduplicatorEngine.generate_fingerprint(job2))

        # 2. Same job_url produces same hash
        job3 = {"job_url": "https://jobs.lever.co/supabase/123", "company": "Supabase", "title": "SDE 1"}
        job4 = {"job_url": "https://jobs.lever.co/supabase/123/", "company": "Supabase Inc", "title": "Backend SDE"}
        self.assertEqual(DeduplicatorEngine.generate_fingerprint(job3), DeduplicatorEngine.generate_fingerprint(job4))

    def test_job_validation(self):
        valid_job = {
            "title": "Software Engineer",
            "company": "Swiggy",
            "job_url": "https://swiggy.com/careers/sde-1",
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
        self.assertIn("https://cred.club/careers/sde1", msg)

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
        self.assertTrue(len(reasons) > 0)

if __name__ == "__main__":
    unittest.main()
