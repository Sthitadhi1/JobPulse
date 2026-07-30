import re
from typing import List, Dict, Any, Optional
from sqlalchemy import select, or_, and_, not_, desc, asc
from backend.app.models.job import Job

class SearchEngine:
    SYNONYM_MAP = {
        "sde": ["Software Engineer", "Software Developer", "Application Developer"],
        "sde 1": ["SDE I", "Software Engineer I", "Junior Software Engineer"],
        "sde 2": ["SDE II", "Software Engineer II", "Senior Developer"],
        "backend": ["Backend Engineer", "Server Engineer", "API Engineer"],
        "frontend": ["Frontend Engineer", "UI Engineer", "Web Developer"],
        "ai": ["Artificial Intelligence", "Machine Learning", "ML Engineer", "LLM Engineer"],
        "ml": ["Machine Learning", "Data Scientist", "AI Engineer"],
        "get": ["Graduate Engineer Trainee", "Campus Graduate", "Management Trainee"]
    }

    @classmethod
    def expand_query_synonyms(cls, query_str: str) -> List[str]:
        tokens = query_str.lower().split()
        expanded = set(tokens)
        for token in tokens:
            if token in cls.SYNONYM_MAP:
                expanded.update([s.lower() for s in cls.SYNONYM_MAP[token]])
        return list(expanded)

    @classmethod
    def calculate_relevance_score(cls, job: Job, query_tokens: List[str]) -> float:
        score = 0.0
        job_text = f"{job.title} {job.company} {job.raw_tags or ''} {job.description or ''}".lower()

        for token in query_tokens:
            if token in job.title.lower():
                score += 30.0 # Exact title match bonus
            elif token in job_text:
                score += 10.0 # General keyword match

        if job.experience_level in ["Fresh Graduate", "0-2 YOE", "Internship"]:
            score += 15.0 # Early career boost for target audience

        return score

    @classmethod
    def build_boolean_conditions(cls, query_str: str):
        """Parse Boolean operators AND, OR, NOT."""
        if not query_str:
            return None

        # Clean string
        raw = query_str.strip()
        
        # Check NOT operator
        if " NOT " in raw:
            parts = raw.split(" NOT ", 1)
            pos_cond = cls.build_boolean_conditions(parts[0])
            neg_cond = cls.build_boolean_conditions(parts[1])
            if pos_cond is not None and neg_cond is not None:
                return and_(pos_cond, not_(neg_cond))

        # Check OR operator
        if " OR " in raw:
            parts = raw.split(" OR ")
            conds = [cls.build_boolean_conditions(p) for p in parts]
            conds = [c for c in conds if c is not None]
            return or_(*conds) if conds else None

        # Check AND operator
        if " AND " in raw:
            parts = raw.split(" AND ")
            conds = [cls.build_boolean_conditions(p) for p in parts]
            conds = [c for c in conds if c is not None]
            return and_(*conds) if conds else None

        # Simple term search across title, company, tags, description
        pattern = f"%{raw}%"
        return or_(
            Job.title.ilike(pattern),
            Job.company.ilike(pattern),
            Job.raw_tags.ilike(pattern),
            Job.description.ilike(pattern)
        )
