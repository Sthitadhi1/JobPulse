import httpx
from typing import List, Dict, Any, Optional
from backend.app.connectors.base import BaseConnector
from backend.app.engine.normalizer import URLNormalizerValidator

class AshbyATSConnector(BaseConnector):
    name: str = "Ashby"
    source_type: str = "ATS"
    version: str = "2.0.0"

    async def stage1_discover(self, company: Dict[str, Any]) -> List[Dict[str, Any]]:
        board_token = company.get("board_token") or company.get("id")
        company_name = company.get("name", board_token)
        careers_url = company.get("careers_url", f"https://jobs.ashbyhq.com/{board_token}")
        discovered = []

        api_url = f"https://api.ashbyhq.com/posting-api/job-board/{board_token}"
        async with httpx.AsyncClient(timeout=6.0, follow_redirects=True) as client:
            try:
                res = await client.get(api_url)
                if res.status_code == 200:
                    data = res.json()
                    for item in data.get("jobs", []):
                        job_id = item.get("id")
                        job_url = item.get("jobUrl", f"https://jobs.ashbyhq.com/{board_token}/{job_id}")
                        clean_url, is_valid, _ = URLNormalizerValidator.resolve_and_validate_url(job_url, careers_url)
                        if is_valid:
                            discovered.append({
                                "company": company_name,
                                "board_token": board_token,
                                "ats_provider": "ashby",
                                "job_url": clean_url,
                                "source_url": careers_url,
                                "raw_item": item
                            })
            except Exception:
                pass
        return discovered

    async def stage2_extract(self, discovery_item: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        raw = discovery_item.get("raw_item", {})
        job_url = discovery_item.get("job_url")
        company_name = discovery_item.get("company")
        board_token = discovery_item.get("board_token")
        source_url = discovery_item.get("source_url")

        title = raw.get("title", "").strip()
        if not title:
            return None

        job_id = raw.get("id")
        location = raw.get("locationName", "Remote")
        dept = raw.get("departmentName")
        description = raw.get("descriptionPlain") or raw.get("descriptionHtml")
        is_remote = raw.get("isRemote", False) or "remote" in location.lower()
        emp_type = raw.get("employmentType", "Full-time")

        # Compensation if explicitly provided by Ashby API
        comp = raw.get("compensation", {})
        sal_str = None
        if comp and comp.get("summary"):
            sal_str = comp.get("summary")

        external_apply_url = f"{job_url}/application" if job_url != "#" else None

        return {
            "external_job_id": f"ashby-{board_token}-{job_id}",
            "title": title,
            "company": company_name,
            "department": dept,
            "location": location,
            "remote_type": "Remote" if is_remote else "Hybrid",
            "employment_type": emp_type,
            "experience_level": None,
            "job_url": job_url,
            "source_url": source_url,
            "external_apply_url": external_apply_url,
            "salary": sal_str, # Official value if present, else None
            "description": description or None,
            "source": self.name,
            "source_type": self.source_type
        }

    async def fetch(self) -> List[Dict[str, Any]]:
        return []
