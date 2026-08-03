import httpx
from typing import List, Dict, Any
from backend.app.connectors.base import BaseConnector

INDIA_REMOTE_KEYWORDS = [
    "india", "bengaluru", "bangalore", "hyderabad", "pune", "mumbai",
    "gurugram", "gurgaon", "noida", "chennai", "delhi", "kolkata",
    "remote", "anywhere", "worldwide", "work from home", "wfh"
]

def is_india_or_remote(location: str) -> bool:
    if not location:
        return True
    loc = location.lower()
    return any(k in loc for k in INDIA_REMOTE_KEYWORDS)

class GreenhouseConnector(BaseConnector):
    name: str = "Greenhouse ATS"
    source_type: str = "ATS"
    version: str = "2.0.0"

    TARGET_COMPANIES = [
        "figma", "stripe", "vercel", "cloudflare", "datadog",
        "rippling", "grammarly", "notion", "retool", "brex",
        "sourcegraph", "postman", "hasura"
    ]

    async def fetch(self) -> List[Dict[str, Any]]:
        jobs = []
        async with httpx.AsyncClient(timeout=5.0) as client:
            for company in self.TARGET_COMPANIES:
                board_url = f"https://boards.greenhouse.io/{company}"
                try:
                    url = f"https://boards-api.greenhouse.io/v1/boards/{company}/jobs?content=true"
                    res = await client.get(url)
                    if res.status_code == 200:
                        data = res.json()
                        for item in data.get("jobs", []):
                            title = item.get("title", "")
                            loc = item.get("location", {}).get("name", "Remote")
                            job_detail_url = item.get("absolute_url", f"{board_url}/jobs/{item.get('id')}")
                            
                            if is_india_or_remote(loc) and any(k in title.lower() for k in ["engineer", "developer", "sde", "intern", "graduate", "ai"]):
                                jobs.append({
                                    "external_job_id": str(item.get("id", "")),
                                    "title": title,
                                    "company": company.capitalize(),
                                    "location": loc,
                                    "remote_type": "Remote" if "remote" in loc.lower() else "Hybrid",
                                    "employment_type": "Full-time",
                                    "job_url": job_detail_url,
                                    "source_url": board_url,
                                    "external_apply_url": None,
                                    "salary": None, # PART 8: No fabricated salary data
                                    "description": f"Greenhouse opportunity for {title} at {company.capitalize()}",
                                    "source": self.name,
                                    "source_type": self.source_type
                                })
                except Exception:
                    continue

        return jobs
