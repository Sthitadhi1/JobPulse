from dataclasses import dataclass
from typing import Optional

@dataclass
class SearchRequest:
    keyword: Optional[str] = None
    location: Optional[str] = None
    min_salary_lpa: Optional[float] = None
    max_salary_lpa: Optional[float] = None
    experience_level: Optional[str] = None
    employment_type: Optional[str] = None
    remote_type: Optional[str] = None
    page: int = 1
    limit: int = 20

    def to_dict(self):
        return {
            "keyword": self.keyword,
            "location": self.location,
            "min_salary_lpa": self.min_salary_lpa,
            "max_salary_lpa": self.max_salary_lpa,
            "experience_level": self.experience_level,
            "employment_type": self.employment_type,
            "remote_type": self.remote_type,
            "page": self.page,
            "limit": self.limit
        }
