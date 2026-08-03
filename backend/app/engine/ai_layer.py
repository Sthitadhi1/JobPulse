import re
from typing import List, Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from backend.app.models.job import Job

class AIEngineLayer:
    """
    Step 19 — Post-Processing AI Layer.
    Operates strictly on indexed database jobs without scraping.
    Provides:
    - Natural Language Search Parsing
    - Resume Keyword Matching & Scoring
    - Skill Gap Analysis
    - Semantic Similarity Ranking
    - Personalized Job Recommendations
    """

    @classmethod
    def parse_natural_language_query(cls, nl_query: str) -> Dict[str, Any]:
        """Parses natural language queries into structured filters."""
        query_lower = nl_query.lower()
        parsed = {
            "keywords": [],
            "experience_level": None,
            "remote_type": None,
            "location": None,
            "min_salary": None
        }

        # Experience level extraction
        if re.search(r'\b(fresher|entry level|0-1|new grad)\b', query_lower):
            parsed["experience_level"] = "Fresher"
        elif re.search(r'\b(intern|internship)\b', query_lower):
            parsed["experience_level"] = "Internship"
        elif re.search(r'\b(senior|sr|lead|principal)\b', query_lower):
            parsed["experience_level"] = "Senior"

        # Remote type extraction
        if "remote" in query_lower:
            parsed["remote_type"] = "Remote"
        elif "hybrid" in query_lower:
            parsed["remote_type"] = "Hybrid"

        # Salary extraction
        sal_match = re.search(r'(\d+)\s*(?:lpa|lakhs|lakh)', query_lower)
        if sal_match:
            parsed["min_salary"] = float(sal_match.group(1))

        # Role keywords
        roles = ["backend", "frontend", "fullstack", "python", "java", "react", "fastapi", "node", "ai", "machine learning", "sde"]
        for r in roles:
            if r in query_lower:
                parsed["keywords"].append(r)

        return parsed

    @classmethod
    def match_resume_to_job(cls, resume_text: str, job: Job) -> Dict[str, Any]:
        """Calculates match score and skill gaps between candidate resume and job posting."""
        resume_words = set(re.findall(r'\b[a-zA-Z0-9+#.]+\b', resume_text.lower()))
        
        job_tags = job.raw_tags.split(", ") if job.raw_tags else []
        job_skills = set(t.lower() for t in job_tags)
        
        if job.skills:
            job_skills.update(s.strip().lower() for s in job.skills.split(","))

        matched_skills = job_skills.intersection(resume_words)
        missing_skills = job_skills.difference(resume_words)

        score = (len(matched_skills) / len(job_skills) * 100.0) if job_skills else 50.0

        return {
            "job_id": job.id,
            "company": job.company,
            "title": job.title,
            "match_score_pct": round(score, 1),
            "matched_skills": sorted([s.capitalize() for s in matched_skills]),
            "missing_skills": sorted([s.capitalize() for s in missing_skills]),
            "recommendation": "Strong Match" if score >= 75 else ("Good Match" if score >= 50 else "Potential Skill Gap")
        }

    @classmethod
    async def get_recommendations(cls, db: AsyncSession, user_skills: List[str], limit: int = 10) -> List[Dict[str, Any]]:
        """Recommends relevant active jobs based on candidate skill set."""
        res = await db.execute(select(Job).where(Job.status == "ACTIVE").limit(100))
        active_jobs = res.scalars().all()

        scored_jobs = []
        user_skills_set = set(s.lower().strip() for s in user_skills)

        for j in active_jobs:
            j_tags = set(t.lower() for t in (j.raw_tags.split(", ") if j.raw_tags else []))
            overlap = len(j_tags.intersection(user_skills_set))
            if overlap > 0:
                scored_jobs.append((j, overlap))

        scored_jobs.sort(key=lambda x: x[1], reverse=True)

        recommendations = []
        for j, score in scored_jobs[:limit]:
            recommendations.append({
                "id": j.id,
                "title": j.title,
                "company": j.company,
                "location": j.location,
                "experience_level": j.experience_level,
                "apply_url": j.external_apply_url or j.job_url,
                "matched_tag_count": score
            })

        return recommendations
