import re
from typing import Dict, Any, Tuple, List, Optional
from urllib.parse import urlparse, urljoin

class URLNormalizerValidator:
    GENERIC_HOMEPAGES = [
        r"^https?://[^/]+/?$",
        r"/careers/?$",
        r"/jobs/?$",
        r"/about/careers/?$",
        r"/boards\.greenhouse\.io/[^/]+/?$",
        r"/jobs\.lever\.co/[^/]+/?$",
        r"/search/?$",
        r"/results/?$"
    ]

    @classmethod
    def resolve_and_validate_url(cls, raw_url: Optional[str], source_url: Optional[str] = None) -> Tuple[str, bool, bool]:
        """
        Resolves relative URLs to absolute URLs and validates individual job link.
        Returns (clean_url, is_valid, was_relative_corrected)
        """
        if not raw_url or raw_url == "#":
            return "#", False, False

        clean_url = raw_url.strip()
        was_relative = False

        # Check if relative URL (starts with / or no scheme)
        parsed = urlparse(clean_url)
        if not parsed.scheme or not parsed.netloc:
            if source_url and source_url != "#":
                clean_url = urljoin(source_url, clean_url)
                parsed = urlparse(clean_url)
                was_relative = True
            else:
                return clean_url, False, False

        if parsed.scheme not in ["http", "https"] or not parsed.netloc:
            return clean_url, False, False

        # Reject generic career homepages or search pages
        for pattern in cls.GENERIC_HOMEPAGES:
            if re.search(pattern, clean_url, re.IGNORECASE):
                return clean_url, False, was_relative

        return clean_url, True, was_relative

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
        return "Fresher / 0-1 YOE"

    @classmethod
    def parse_salary(cls, salary_str: Optional[str], title: str) -> Tuple[Optional[str], Optional[float], Optional[float]]:
        if not salary_str:
            if any(k in title.lower() for k in ["sde", "software", "backend", "frontend", "ai", "data"]):
                return "₹8 - ₹14 LPA (Est.)", 8.0, 14.0
            return "Salary Disclosed on Application", None, None

        salary_clean = salary_str.strip()
        
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
        raw_title = raw_job.get("title", "")
        raw_desc = raw_job.get("description", "")
        
        norm_title = cls.normalize_title(raw_title)
        exp_level = cls.detect_experience_level(norm_title, raw_desc)
        salary_fmt, min_sal, max_sal = cls.parse_salary(raw_job.get("salary"), norm_title)
        tags = cls.extract_tags(norm_title, raw_desc)

        source_url = raw_job.get("source_url") or raw_job.get("url") or "#"
        raw_job_url = raw_job.get("job_url") or raw_job.get("url") or "#"
        raw_apply_url = raw_job.get("external_apply_url")

        # Resolve & Validate job_url
        clean_job_url, job_url_valid, _ = URLNormalizerValidator.resolve_and_validate_url(raw_job_url, source_url)
        clean_apply_url, apply_url_valid, _ = URLNormalizerValidator.resolve_and_validate_url(raw_apply_url, source_url) if raw_apply_url else ("#", False, False)

        final_job_url = clean_job_url if job_url_valid else (clean_apply_url if apply_url_valid else "#")
        final_external_apply_url = clean_apply_url if apply_url_valid else None

        return {
            "external_job_id": raw_job.get("external_job_id"),
            "title": norm_title,
            "company": raw_job.get("company", "Unknown"),
            "location": raw_job.get("location", "India / Remote"),
            "remote_type": raw_job.get("remote_type", "Hybrid"),
            "employment_type": raw_job.get("employment_type", "Full-time"),
            "experience_level": exp_level,
            "salary_range": salary_fmt,
            "min_salary_lpa": min_sal,
            "max_salary_lpa": max_sal,
            "job_url": final_job_url,
            "source_url": source_url,
            "external_apply_url": final_external_apply_url,
            "apply_url": final_external_apply_url or final_job_url,
            "canonical_url": final_job_url,
            "source": raw_job.get("source", "Connector"),
            "source_type": raw_job.get("source_type", "ATS"),
            "raw_tags": ", ".join(tags),
            "description": raw_desc
        }
