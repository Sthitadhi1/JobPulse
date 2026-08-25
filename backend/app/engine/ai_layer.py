import re
import json
from typing import List, Dict, Any, Optional, Set, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from backend.app.models.job import Job
from backend.app.engine.resume_parser import ResumeParserEngine

class AIEngineLayer:
    """
    JobPulse AI Intelligence & Dynamic Match Engine.
    Performs 7-part weighted candidate-to-job matching with full text extraction,
    semantic skill expansion, role domain classification, experience gap analysis,
    and granular score breakdowns.
    Evaluates against ACTIVE jobs only.
    """

    SKILL_SYNONYMS = {
        "machine learning": {"ml", "machine learning", "applied machine learning", "deep learning", "pytorch", "tensorflow", "scikit-learn", "ai", "artificial intelligence", "data science"},
        "ml": {"ml", "machine learning", "applied machine learning", "deep learning", "pytorch", "tensorflow", "scikit-learn", "ai"},
        "deep learning": {"deep learning", "neural networks", "pytorch", "tensorflow", "keras", "computer vision", "nlp"},
        "rest api": {"rest api", "restful apis", "rest api development", "fastapi", "flask", "express", "api development", "graphql", "microservices"},
        "react": {"react", "react.js", "next.js", "redux", "frontend", "typescript", "javascript", "tailwind", "html", "css"},
        "next.js": {"next.js", "react", "react.js", "ssr", "typescript", "frontend"},
        "python": {"python", "django", "fastapi", "flask", "pandas", "numpy", "pytorch"},
        "java": {"java", "spring boot", "spring", "jvm", "microservices", "hibernate"},
        "c++": {"c++", "cpp", "c", "embedded", "data structures", "algorithms"},
        "aws": {"aws", "amazon web services", "cloud", "ec2", "s3", "lambda", "gcp", "azure", "docker", "kubernetes"},
        "sql": {"sql", "postgresql", "postgres", "mysql", "sqlite", "database", "mongodb", "redis", "rdbms"},
        "docker": {"docker", "containerization", "kubernetes", "k8s", "ci/cd", "devops"},
        "kubernetes": {"kubernetes", "k8s", "docker", "cloud", "devops", "helm", "terraform"},
        "devops": {"devops", "docker", "kubernetes", "k8s", "ci/cd", "git", "github actions", "terraform", "linux"}
    }

    ROLE_DOMAINS = {
        "backend": ["backend", "api", "distributed", "server", "microservices", "java", "python", "golang", "node", "django", "fastapi", "spring"],
        "frontend": ["frontend", "react", "ui", "ux", "angular", "vue", "javascript", "typescript", "web", "css", "html", "next.js"],
        "fullstack": ["full stack", "fullstack", "software engineer", "sde", "software developer", "web developer"],
        "ai_ml": ["machine learning", "ml", "ai", "data scientist", "deep learning", "nlp", "computer vision", "research engineer", "llm"],
        "data": ["data engineer", "data analyst", "etl", "big data", "spark", "hadoop", "sql", "snowflake"],
        "devops": ["devops", "cloud", "infrastructure", "sre", "reliability", "platform", "kubernetes", "docker", "aws"],
        "mobile": ["android", "ios", "flutter", "react native", "swift", "kotlin", "mobile"],
        "security": ["security", "cyber", "infosec", "penetration", "soc", "cryptography"],
        "qa": ["qa", "quality assurance", "test", "automation", "sdet", "selenium"]
    }

    @classmethod
    def expand_skills_semantically(cls, skills: List[str]) -> Set[str]:
        expanded = set()
        for sk in skills:
            sk_lower = sk.lower().strip()
            expanded.add(sk_lower)
            if sk_lower in cls.SKILL_SYNONYMS:
                expanded.update(cls.SKILL_SYNONYMS[sk_lower])
            for main_sk, syns in cls.SKILL_SYNONYMS.items():
                if sk_lower in syns:
                    expanded.update(syns)
        return expanded

    @classmethod
    def extract_job_skills(cls, job: Job) -> Set[str]:
        """
        Dynamically extracts all technology skills and requirements from
        job tags, skills column, job title, and full description text.
        """
        found_skills = set()

        if job.skills:
            for s in job.skills.split(","):
                if s.strip():
                    found_skills.add(s.strip())

        if job.raw_tags:
            for t in job.raw_tags.split(","):
                if t.strip():
                    found_skills.add(t.strip())

        # Scan text of title and description for standard technologies
        text_to_scan = f"{job.title or ''} {job.description or ''}"
        for cat, kw_list in ResumeParserEngine.TECH_KEYWORDS.items():
            for kw in kw_list:
                pattern = r'\b' + re.escape(kw) + r'\b'
                if re.search(pattern, text_to_scan, re.IGNORECASE):
                    found_skills.add(kw)

        return found_skills

    @classmethod
    def classify_role_domain(cls, text: str) -> str:
        text_lower = text.lower()
        scores = {}
        for domain, keywords in cls.ROLE_DOMAINS.items():
            count = sum(1 for kw in keywords if kw in text_lower)
            if count > 0:
                scores[domain] = count

        if scores:
            return max(scores, key=scores.get)
        return "fullstack"

    @classmethod
    def match_candidate_to_job(cls, candidate_profile: Dict[str, Any], job: Job) -> Dict[str, Any]:
        """
        Calculates realistic 7-part weighted match score between candidate profile and an ACTIVE job.
        Model Weights:
        - Skill Match: 35%
        - Experience Match: 20%
        - Role Match: 15%
        - Education Match: 10%
        - Location / Work Mode: 10%
        - Seniority Alignment: 5%
        - Salary Alignment: 5%
        """
        cand_skills = candidate_profile.get("skills", [])
        expanded_cand_skills = cls.expand_skills_semantically(cand_skills)

        # 1. Extract and Evaluate Job Skills (35% weight)
        job_skills = cls.extract_job_skills(job)
        matching_skills = []
        missing_skills = []

        if job_skills:
            for js in job_skills:
                js_lower = js.lower()
                expanded_js = cls.expand_skills_semantically([js])
                if expanded_cand_skills.intersection(expanded_js) or js_lower in expanded_cand_skills:
                    matching_skills.append(js)
                else:
                    missing_skills.append(js)

            ratio = len(matching_skills) / max(1, len(job_skills))
            # Skill Score formula: Base proportion + language overlap bonus
            skill_score = min(95.0, (ratio * 75.0) + (min(len(matching_skills), 4) * 5.0))
            if len(matching_skills) == 0:
                skill_score = max(15.0, min(35.0, 10.0 + len(cand_skills)))
        else:
            # General software role without explicit tech keywords
            matching_skills = [s for s in cand_skills[:4]]
            missing_skills = []
            skill_score = 72.0

        # 2. Experience Match (20% weight)
        cand_exp = (candidate_profile.get("experience_level") or "Fresher").lower()
        cand_yoe = candidate_profile.get("experience_years", 0)

        job_title_lower = (job.title or "").lower()
        job_exp_lower = (job.experience_level or "").lower()

        is_job_senior = any(w in job_title_lower for w in ["senior", "staff", "principal", "lead", "architect", "manager", "head of", "director"]) or "senior" in job_exp_lower
        is_job_mid = any(w in job_title_lower for w in ["mid", "sde 2", "sde ii", "sde2", "engineer ii", "level 2"]) or "mid" in job_exp_lower
        is_job_entry = any(w in job_title_lower for w in ["intern", "internship", "fresher", "entry", "graduate", "trainee", "associate", "sde 1", "sde i", "sde1", "junior"]) or "fresher" in job_exp_lower or "intern" in job_exp_lower or "associate" in job_exp_lower

        if "senior" in cand_exp or cand_yoe >= 4:
            if is_job_senior:
                exp_score = 95.0
            elif is_job_mid:
                exp_score = 85.0
            else:
                exp_score = 65.0
        elif "mid" in cand_exp or cand_yoe >= 2:
            if is_job_senior:
                exp_score = 50.0
            elif is_job_mid or is_job_entry:
                exp_score = 92.0
            else:
                exp_score = 75.0
        else:
            # Candidate is Fresher / Intern / Entry
            if is_job_senior:
                exp_score = 25.0
            elif is_job_mid:
                exp_score = 55.0
            elif is_job_entry:
                exp_score = 95.0
            else:
                exp_score = 80.0

        # 3. Role & Title Alignment (15% weight)
        cand_pref_roles = candidate_profile.get("preferred_roles", [])
        cand_domains = [cls.classify_role_domain(r) for r in cand_pref_roles]
        if not cand_domains:
            cand_domains = [cls.classify_role_domain(" ".join(cand_skills))]

        job_domain = cls.classify_role_domain(f"{job.title} {job.description}")

        if job_domain in cand_domains:
            role_score = 92.0
        elif any(d in ["fullstack", "backend"] for d in cand_domains) and job_domain in ["fullstack", "backend", "frontend"]:
            role_score = 78.0
        elif any(d in ["ai_ml", "data"] for d in cand_domains) and job_domain in ["ai_ml", "data", "backend"]:
            role_score = 75.0
        elif any(d in ["devops"] for d in cand_domains) and job_domain in ["devops", "backend"]:
            role_score = 75.0
        elif any(w in job_title_lower for w in ["marketing", "sales", "finance", "legal", "hr", "recruiter", "operations"]):
            role_score = 20.0
        else:
            role_score = 60.0

        # 4. Education Match (10% weight)
        cand_degree = (candidate_profile.get("degree") or "").lower()
        if "phd" in job_title_lower:
            edu_score = 45.0
        elif "computer science" in cand_degree or "b.tech" in cand_degree or "bachelor" in cand_degree or "m.tech" in cand_degree:
            edu_score = 90.0
        else:
            edu_score = 75.0

        # 5. Location / Work Mode (10% weight)
        job_loc = (job.location or "").lower()
        if job.remote_type == "Remote" or "remote" in job_loc:
            loc_score = 95.0
        elif any(city in job_loc for city in ["india", "bengaluru", "bangalore", "hyderabad", "pune", "mumbai", "delhi", "noida", "gurugram", "chennai"]):
            loc_score = 90.0
        else:
            loc_score = 65.0

        # 6. Seniority Fit (5% weight)
        seniority_score = exp_score

        # 7. Salary Alignment (5% weight)
        sal_score = 80.0
        if job.min_salary_lpa:
            sal_score = 90.0 if job.min_salary_lpa >= 6.0 else 75.0

        # Overall Weighted Score calculation
        total_score = (
            (skill_score * 0.35) +
            (exp_score * 0.20) +
            (role_score * 0.15) +
            (edu_score * 0.10) +
            (loc_score * 0.10) +
            (seniority_score * 0.05) +
            (sal_score * 0.05)
        )
        total_score = round(min(94.5, max(38.0, total_score)), 1)

        # Classification & Priority
        if total_score >= 84.0:
            classification = "Strong Match"
            priority = "HIGH"
        elif total_score >= 70.0:
            classification = "Good Match"
            priority = "HIGH" if total_score >= 76.0 else "MEDIUM"
        elif total_score >= 55.0:
            classification = "Moderate Match"
            priority = "MEDIUM"
        else:
            classification = "Weak Match"
            priority = "LOW"

        # Tailored Explanations
        if matching_skills:
            matched_str = ", ".join(matching_skills[:4])
            why_matches = f"Your background in {matched_str} aligns directly with {job.company}'s requirements for {job.title}."
        else:
            why_matches = f"Your engineering background and technical foundation match the requirements for {job.title} at {job.company}."

        if missing_skills:
            potential_gap = f"The position highlights {', '.join(missing_skills[:3])}, which are not prominent in your resume."
        else:
            potential_gap = "Your candidate profile satisfies the core technical requirements for this role."

        return {
            "job_id": job.id,
            "title": job.title,
            "company": job.company,
            "location": job.location,
            "remote_type": job.remote_type,
            "employment_type": job.employment_type,
            "experience_level": job.experience_level,
            "salary_range": job.salary_range,
            "min_salary_lpa": job.min_salary_lpa,
            "job_url": job.job_url,
            "apply_url": job.external_apply_url or job.job_url,
            "source": job.source,
            "status": job.status,
            "verification_status": job.verification_status,
            "is_bookmarked": job.is_bookmarked,
            "match_score": total_score,
            "match_classification": classification,
            "application_priority": priority,
            "breakdown": {
                "skill_match": round(skill_score, 1),
                "role_alignment": round(role_score, 1),
                "experience_match": round(exp_score, 1),
                "education_match": round(edu_score, 1),
                "location_match": round(loc_score, 1),
                "salary_match": round(sal_score, 1),
                "overall": total_score
            },
            "matching_skills": matching_skills,
            "missing_skills": missing_skills,
            "why_matches": why_matches,
            "potential_gap": potential_gap
        }

    @classmethod
    async def get_top_30_recommendations(cls, db: AsyncSession, candidate_profile: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Queries ACTIVE jobs ONLY, evaluates matching, and returns top 30 recommendations sorted by match score.
        """
        res = await db.execute(select(Job).where(Job.status == "ACTIVE").limit(350))
        active_jobs = res.scalars().all()

        evaluated = []
        for j in active_jobs:
            m_res = cls.match_candidate_to_job(candidate_profile, j)
            evaluated.append(m_res)

        evaluated.sort(key=lambda x: x["match_score"], reverse=True)
        return evaluated[:30]
