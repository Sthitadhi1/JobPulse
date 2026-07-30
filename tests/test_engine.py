import unittest
import asyncio
from backend.app.engine.normalizer import NormalizerEngine
from backend.app.engine.deduplicator import DeduplicatorEngine
from backend.app.engine.search import SearchEngine
from backend.app.engine.matching import MatchingEngine
from backend.app.models.job import Job, SavedSearch

class TestJobPulseEngine(unittest.TestCase):
    def test_normalizer_salary_and_experience(self):
        raw = {
            "title": "Junior Backend Engineer (SDE 1)",
            "company": "Tech Corp",
            "location": "Bengaluru",
            "salary": "₹12 - ₹16 LPA",
            "description": "Building microservices with Python, FastAPI, Docker, and PostgreSQL."
        }
        normalized = NormalizerEngine.normalize_job_data(raw)
        self.assertEqual(normalized["experience_level"], "Fresh Graduate")
        self.assertEqual(normalized["min_salary_lpa"], 12.0)
        self.assertEqual(normalized["max_salary_lpa"], 16.0)
        self.assertIn("Python", normalized["raw_tags"])

    def test_deduplicator_fingerprint(self):
        fp1 = DeduplicatorEngine.generate_fingerprint("Razorpay", "Software Engineer", "Bengaluru")
        fp2 = DeduplicatorEngine.generate_fingerprint("razorpay", "software engineer", "bengaluru")
        self.assertEqual(fp1, fp2)

    def test_boolean_search_conditions(self):
        cond = SearchEngine.build_boolean_conditions("Backend AND Python NOT Senior")
        self.assertIsNotNone(cond)

    def test_matching_engine_evaluation(self):
        job = Job(
            title="Software Development Engineer 1 (SDE I)",
            company="Razorpay",
            location="Bengaluru",
            remote_type="Hybrid",
            experience_level="Fresh Graduate",
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
            experience_level="Fresh Graduate"
        )
        is_match, score, reasons = MatchingEngine.evaluate_job_against_search(job, search)
        self.assertTrue(is_match)
        self.assertGreater(score, 0)
        self.assertTrue(len(reasons) > 0)

if __name__ == "__main__":
    unittest.main()
