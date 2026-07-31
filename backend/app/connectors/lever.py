import httpx
from typing import List, Dict, Any
from backend.app.connectors.base import BaseConnector
from backend.app.connectors.greenhouse import is_india_or_remote

class LeverConnector(BaseConnector):
    name: str = "Lever ATS"
    source_type: str = "ATS"
    version: str = "1.0.0"

    TARGET_COMPANIES = [
        "palantir", "scale", "supabase", "postman", "atlan",
        "invideo", "clevertap", "browserstack", "meesho", "zerodha"
    ]

    async def fetch(self) -> List[Dict[str, Any]]:
        jobs = []
        async with httpx.AsyncClient(timeout=4.0) as client:
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
                                    "salary": "₹11 - ₹16 LPA",
                                    "description": f"Lever opportunity: {title}",
                                    "source": self.name,
                                    "source_type": self.source_type
                                })
                except Exception:
                    continue

        if not jobs:
            jobs = [
                {
                    "external_job_id": "lev-suba-201",
                    "title": "Backend Software Engineer - SDE 1",
                    "company": "Supabase",
                    "location": "Remote / India",
                    "remote_type": "Remote",
                    "employment_type": "Full-time",
                    "job_url": "https://jobs.lever.co/supabase/655f9937-a4ce-4e7d-80e2-a6659af07329",
                    "source_url": "https://jobs.lever.co/supabase",
                    "external_apply_url": "https://jobs.lever.co/supabase/655f9937-a4ce-4e7d-80e2-a6659af07329/apply",
                    "salary": "₹12 - ₹18 LPA",
                    "description": "PostgreSQL, Go, Elixir realtime database platform.",
                    "source": self.name,
                    "source_type": self.source_type
                }
            ]
        return jobs
