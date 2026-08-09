import re
from typing import Dict, Any, Tuple, List, Optional
from urllib.parse import urlparse, urljoin

class URLNormalizerValidator:
    GENERIC_HOMEPAGES = [
        r"^https?://[^/]+/?$",
        r"/careers/?$",
        r"/jobs/?$",
        r"/about/careers/?$",
        r"/job-openings/?$",
        r"/boards\.greenhouse\.io/[^/]+/?$",
        r"/jobs\.lever\.co/[^/]+/?$",
        r"/search/?$",
        r"/results/?$",
        r"\?department=",
        r"\?category=",
        r"\?search=",
        r"\?query=",
        r"\?filter=",
        r"/careers/job-openings"
    ]

    TRACKING_PARAMS = [
        r"utm_[a-z]+=[^&]*",
        r"refid=[^&]*",
        r"trackingid=[^&]*",
        r"sessionid=[^&]*",
        r"gh_src=[^&]*",
        r"position=[^&]*",
        r"pagenum=[^&]*"
    ]

    @classmethod
    def strip_tracking_params(cls, url: str) -> str:
        clean = url
        for p in cls.TRACKING_PARAMS:
            clean = re.sub(r'([?&])' + p + r'&?', r'\1', clean, flags=re.IGNORECASE)
        clean = re.sub(r'[?&]$', '', clean)
        return clean

    @classmethod
    def resolve_and_validate_url(cls, raw_url: Optional[str], source_url: Optional[str] = None) -> Tuple[str, bool, bool]:
        """
        Resolves relative URLs to absolute URLs, strips tracking parameters, and validates individual job link.
        Returns (clean_url, is_valid, was_relative_corrected)
        """
        if not raw_url or raw_url == "#":
            return "#", False, False

        clean_url = cls.strip_tracking_params(raw_url.strip())
        was_relative = False

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
    VALID_EXPERIENCE_CATEGORIES = [
        "Internship",
        "Campus Hiring",
        "Fresher",
        "Associate",
        "Mid-Level",
        "Senior",
        "Lead",
        "Staff",
        "Principal",
        "Manager",
        "Director",
        "Vice President",
        "Distinguished Engineer",
        "Fellow"
    ]

    TECH_TAGS = [
        "Python", "Java", "C++", "Go", "Rust", "TypeScript", "JavaScript",
        "React", "Node.js", "FastAPI", "Django", "Flask", "Spring Boot",
        "Docker", "Kubernetes", "AWS", "GCP", "PostgreSQL", "MongoDB",
        "Machine Learning", "AI", "PyTorch", "TensorFlow", "SQL", "Redis",
        "DevOps", "Cybersecurity", "Microservices"
    ]

    @classmethod
    def normalize_title(cls, raw_title: str) -> str:
        title = raw_title.strip()
        title = re.sub(r'\s+', ' ', title)
        return title

    @classmethod
    def detect_experience_level(cls, title: str, description: str = "", explicit_level: Optional[str] = None) -> str:
        if explicit_level and explicit_level.strip():
            clean_exp = explicit_level.strip()
            if "Fresher" in clean_exp or "0-1" in clean_exp:
                return "Fresher"
            if "2-4" in clean_exp or "Mid" in clean_exp:
                return "Mid-Level"
            if "4+" in clean_exp or "Senior" in clean_exp:
                return "Senior"
            for cat in cls.VALID_EXPERIENCE_CATEGORIES:
                if cat.lower() in clean_exp.lower():
                    return cat

        text = f"{title} {description}".lower()

        if re.search(r'\b(distinguished engineer|distinguished)\b', text):
            return "Distinguished Engineer"
        if re.search(r'\b(fellow)\b', text):
            return "Fellow"
        if re.search(r'\b(vice president|vp)\b', text):
            return "Vice President"
        if re.search(r'\b(director)\b', text):
            return "Director"
        if re.search(r'\b(manager|engineering manager|tech manager)\b', text):
            return "Manager"
        if re.search(r'\b(principal)\b', text):
            return "Principal"
        if re.search(r'\b(staff engineer|staff)\b', text):
            return "Staff"
        if re.search(r'\b(tech lead|team lead|lead engineer|lead)\b', text):
            return "Lead"

        yoe_match = re.search(r'(\d+)\s*(?:-|to|–|\+)?\s*(\d+)?\s*(?:years?|yrs?)\s*(?:of\s*)?(?:experience|exp)?', text)
        if yoe_match:
            min_yoe = int(yoe_match.group(1))
            max_yoe = int(yoe_match.group(2)) if yoe_match.group(2) else min_yoe

            if min_yoe >= 8 or max_yoe >= 10:
                return "Principal"
            if min_yoe >= 5:
                return "Senior"
            if min_yoe in [1, 2, 3, 4] or max_yoe in [2, 3, 4, 5]:
                if re.search(r'\b(senior|sr)\b', text):
                    return "Senior"
                return "Mid-Level"

        if re.search(r'\b(senior|sr\.|sr\b|sde 3|sde iii|software engineer 3|architect)\b', text):
            return "Senior"

        if re.search(r'\b(1-3|2-4|1 - 3|2 - 4|mid level|mid-level|sde 2|sde ii|software engineer 2|intermediate)\b', text):
            return "Mid-Level"

        if re.search(r'\b(intern|internship|co-op|summer intern)\b', text):
            return "Internship"

        if re.search(r'\b(campus|trainee|get|university|graduate program|campus hiring|graduate engineer)\b', text):
            return "Campus Hiring"

        if re.search(r'\b(fresher|entry level|0-1|0 - 1|new grad|fresh graduate)\b', text):
            return "Fresher"

        if re.search(r'\b(associate|sde 1|sde i|software engineer 1|software engineer i|junior|jr)\b', text):
            return "Associate"

        return "Fresher"

    @classmethod
    def parse_salary(cls, salary_str: Optional[str], title: str) -> Tuple[Optional[str], Optional[float], Optional[float]]:
        if not salary_str:
            return None, None, None

        salary_clean = salary_str.strip()
        if not salary_clean or salary_clean == "#":
            return None, None, None
        
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
        explicit_exp = raw_job.get("experience_level")
        
        norm_title = cls.normalize_title(raw_title)
        exp_level = cls.detect_experience_level(norm_title, raw_desc, explicit_exp)
        salary_fmt, min_sal, max_sal = cls.parse_salary(raw_job.get("salary"), norm_title)
        tags = cls.extract_tags(norm_title, raw_desc)

        source_url = raw_job.get("source_url") or raw_job.get("url") or "#"
        raw_job_url = raw_job.get("job_url") or raw_job.get("url") or "#"
        raw_apply_url = raw_job.get("external_apply_url")

        clean_job_url, job_url_valid, _ = URLNormalizerValidator.resolve_and_validate_url(raw_job_url, source_url)
        clean_apply_url, apply_url_valid, _ = URLNormalizerValidator.resolve_and_validate_url(raw_apply_url, source_url) if raw_apply_url else ("#", False, False)

        final_job_url = clean_job_url if job_url_valid else (clean_apply_url if apply_url_valid else "#")
        final_external_apply_url = clean_apply_url if apply_url_valid else None

        return {
            "external_job_id": raw_job.get("external_job_id"),
            "title": norm_title,
            "company": raw_job.get("company", "Unknown"),
            "department": raw_job.get("department"),
            "location": raw_job.get("location", "India / Remote"),
            "country": raw_job.get("country", "India"),
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
            "skills": raw_job.get("skills") or ", ".join(tags),
            "benefits": raw_job.get("benefits"),
            "description": raw_desc,
            "status": raw_job.get("status", "ACTIVE"),
            "verification_status": raw_job.get("verification_status", "VERIFIED")
        }
