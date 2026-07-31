import datetime
from typing import Dict, Any, List, Tuple
from backend.app.models.job import Job, SavedSearch

class MatchingEngine:
    @classmethod
    def evaluate_job_against_search(cls, job: Job, search: SavedSearch) -> Tuple[bool, float, List[str]]:
        reasons = []
        score = 0.0

        # Mandatory Filter: Location
        if search.location:
            req_loc = search.location.lower()
            if req_loc not in job.location.lower() and req_loc not in (job.remote_type or "").lower():
                return False, 0.0, []
            reasons.append(f"Location match: {job.location}")
            score += 10.0

        # Mandatory Filter: Remote Type
        if search.remote_type:
            if search.remote_type.lower() not in (job.remote_type or "").lower():
                return False, 0.0, []
            reasons.append(f"Remote preference: {job.remote_type}")
            score += 10.0

        # Mandatory Filter: Min Salary LPA
        if search.min_salary_lpa and job.min_salary_lpa:
            if job.min_salary_lpa < search.min_salary_lpa:
                return False, 0.0, []
            reasons.append(f"Salary match: ₹{job.min_salary_lpa} LPA")
            score += 10.0

        # Mandatory Filter: Experience Level
        if search.experience_level:
            exp_search = search.experience_level.lower()
            exp_job = (job.experience_level or "").lower()
            
            fresher_terms = ["fresher", "fresh", "0-1", "entry", "internship", "0-2"]
            mid_terms = ["2-4", "mid"]
            high_terms = ["4+", "high", "senior"]

            is_search_fresher = any(k in exp_search for k in fresher_terms)
            is_job_fresher = any(k in exp_job for k in fresher_terms)

            is_search_mid = any(k in exp_search for k in mid_terms)
            is_job_mid = any(k in exp_job for k in mid_terms)

            is_search_high = any(k in exp_search for k in high_terms)
            is_job_high = any(k in exp_job for k in high_terms)

            if is_search_fresher and is_job_fresher:
                pass
            elif is_search_mid and is_job_mid:
                pass
            elif is_search_high and is_job_high:
                pass
            elif exp_search in exp_job or exp_job in exp_search:
                pass
            else:
                return False, 0.0, []

            reasons.append(f"Experience level: {job.experience_level}")
            score += 15.0

        # Keyword / Title Matching
        if search.keywords or search.query:
            query_str = (search.keywords or search.query or "").lower()
            matched_keywords = []

            for kw in query_str.replace("and", "").replace("or", "").split():
                clean_kw = kw.strip()
                if not clean_kw:
                    continue
                if clean_kw in job.title.lower():
                    matched_keywords.append(clean_kw)
                    score += 30.0
                elif clean_kw in (job.raw_tags or "").lower() or clean_kw in (job.description or "").lower():
                    matched_keywords.append(clean_kw)
                    score += 20.0

            if matched_keywords:
                reasons.append(f"Matched keywords: {', '.join(set(matched_keywords))}")
            elif search.query and (" and " in search.query.lower()):
                return False, 0.0, []

        return True, score, reasons
