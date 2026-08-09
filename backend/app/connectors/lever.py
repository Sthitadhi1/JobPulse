import httpx
from typing import List, Dict, Any, Optional
from backend.app.connectors.base import BaseConnector
from backend.app.connectors.greenhouse import is_india_or_remote

class LeverConnector(BaseConnector):
    name: str = "Lever ATS"
    source_type: str = "ATS"
    version: str = "2.0.0"

    TARGET_COMPANIES = [
        "palantir", "scale", "supabase", "postman", "atlan",
        "invideo", "clevertap", "browserstack", "meesho", "zerodha"
    ]

    async def stage1_discover(self, company: Dict[str, Any]) -> List[Dict[str, Any]]:
        return []

    async def stage2_extract(self, discovery_item: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        return None

    async def fetch(self) -> List[Dict[str, Any]]:
        jobs = []
        async with httpx.AsyncClient(timeout=5.0) as client:
            for company in self.TARGET_COMPANIES:
                board_url = f"https://jobs.lever.co/{company}"
                try:
                    url = f"https://api.lever.co/v0/postings/{company}?mode=json"
                    res = await client.get(url)
                    if res.status_code == 200:
                        data = res.json()
                        for item in data:
                            title = item.get("text", "")
                            loc = item.get("categories", {}).get("location", "Remote")
                            job_detail_url = item.get("hostedUrl", f"{board_url}/{item.get('id')}")
                            
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
                                    "external_apply_url": f"{job_detail_url}/apply" if job_detail_url != "#" else None,
                                    "salary": None, # PART 8: No fabricated salary data
                                    "description": f"Lever opportunity: {title}",
                                    "source": self.name,
                                    "source_type": self.source_type
                                })
                except Exception:
                    continue

        return jobs
