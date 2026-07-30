import re
from typing import Dict, Any, Tuple, List, Optional

class NormalizerEngine:
    EXPERIENCE_KEYWORDS = {
        "Fresher / 0-1 YOE": [r"intern", r"co-op", r"trainee", r"graduate", r"fresher", r"entry level", r"junior", r"associate", r"sde 1", r"sde i", r"software engineer 1", r"0-1", r"0 - 1"],
        "2-4 YOE (Mid Level)": [r"2-4", r"2 - 4", r"1-3", r"1 - 3", r"mid level", r"sde ii", r"sde 2", r"software engineer 2", r"intermediate"],
        "4+ YOE (High Exp)": [r"senior", r"staff", r"lead", r"principal", r"manager", r"architect", r"4\+", r"5\+", r"3\+"]
    }

    TECH_TAGS = [
        "Python", "Java", "C++", "Go", "Rust", "TypeScript", "JavaScript",
        "React", "Node.js", "FastAPI", "Django", "Flask", "Spring Boot",
        "Docker", "Kubernetes", "AWS", "GCP", "PostgreSQL", "MongoDB",
        "Machine Learning", "AI", "PyTorch", "TensorFlow", "SQL", "Redis"
    ]

    @classmethod
    def normalize_title(cls, raw_title: str) -> str:
        title = raw_title.strip()
        title = re.sub(r'\s+', ' ', title)
        return title

    @classmethod
    def detect_experience_level(cls, title: str, description: str = "") -> str:
        text = f"{title} {description}".lower()
        for level, patterns in cls.EXPERIENCE_KEYWORDS.items():
            for pattern in patterns:
                if re.search(r'\b' + pattern + r'\b', text):
                    return level
        return "Fresh Graduate"

    @classmethod
    def parse_salary(cls, salary_str: Optional[str], title: str) -> Tuple[Optional[str], Optional[float], Optional[float]]:
        if not salary_str:
            if any(k in title.lower() for k in ["sde", "software", "backend", "frontend", "ai", "data"]):
                return "₹8 - ₹14 LPA (Est.)", 8.0, 14.0
            return "Salary Disclosed on Application", None, None

        salary_clean = salary_str.strip()
        
        # Match range e.g. "12 - 16 LPA" or "₹12 - ₹16 LPA"
        lpa_range = re.search(r'(\d+(?:\.\d+)?)\s*(?:-|to|–)\s*(?:[₹$INR]+\s*)?(\d+(?:\.\d+)?)\s*(?:LPA|Lakh|Lakhs)', salary_clean, re.IGNORECASE)
        if lpa_range:
            min_sal = float(lpa_range.group(1))
            max_sal = float(lpa_range.group(2))
            if min_sal > max_sal:
                min_sal, max_sal = max_sal, min_sal
            return f"₹{min_sal:g} - ₹{max_sal:g} LPA", min_sal, max_sal

        single_lpa = re.search(r'(\d+(?:\.\d+)?)\s*(?:LPA|Lakh|Lakhs)', salary_clean, re.IGNORECASE)
        if single_lpa:
            sal = float(single_lpa.group(1))
            return f"₹{sal:g} LPA", sal, sal

        return salary_clean, None, None

    @classmethod
    def extract_tags(cls, title: str, description: str = "") -> List[str]:
        text = f"{title} {description}"
        tags = []
        for tag in cls.TECH_TAGS:
            pattern = r'\b' + re.escape(tag) + r'\b'
            if re.search(pattern, text, re.IGNORECASE):
                tags.append(tag)
        return tags if tags else ["Software Engineering", "Tech"]

    @classmethod
    def normalize_job_data(cls, raw_job: Dict[str, Any]) -> Dict[str, Any]:
        title = cls.normalize_title(raw_job.get("title", "Software Engineer"))
        company = raw_job.get("company", "Tech Company").strip()
        location = raw_job.get("location", "Remote / Hybrid").strip()
        description = raw_job.get("description", "")
        
        exp_level = cls.detect_experience_level(title, description)
        salary_fmt, min_sal, max_sal = cls.parse_salary(raw_job.get("salary"), title)
        tags = cls.extract_tags(title, description)

        return {
            "external_job_id": raw_job.get("external_job_id"),
            "title": title,
            "company": company,
            "location": location,
            "remote_type": raw_job.get("remote_type", "Hybrid"),
            "employment_type": raw_job.get("employment_type", "Full-time"),
            "experience_level": exp_level,
            "salary_range": salary_fmt,
            "min_salary_lpa": min_sal,
            "max_salary_lpa": max_sal,
            "apply_url": raw_job.get("url", "#"),
            "canonical_url": raw_job.get("url", "#"),
            "source": raw_job.get("source", "Connector"),
            "source_type": raw_job.get("source_type", "ATS"),
            "raw_tags": ", ".join(tags),
            "description": description
        }
