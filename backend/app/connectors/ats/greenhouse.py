import httpx
from typing import List, Dict, Any, Optional
from backend.app.connectors.base import BaseConnector
from backend.app.engine.normalizer import URLNormalizerValidator

class GreenhouseATSConnector(BaseConnector):
    name: str = "Greenhouse"
    source_type: str = "ATS"
    version: str = "2.1.0"

    async def stage1_discover(self, company: Dict[str, Any]) -> List[Dict[str, Any]]:
        board_token = company.get("board_token") or company.get("id")
        company_name = company.get("name", board_token)
        careers_url = company.get("careers_url", f"https://boards.greenhouse.io/{board_token}")

        discovered = []
        api_url = f"https://boards-api.greenhouse.io/v1/boards/{board_token}/jobs?content=true"

        async with httpx.AsyncClient(timeout=6.0, follow_redirects=True) as client:
            try:
                res = await client.get(api_url)
                if res.status_code == 200:
                    data = res.json()
                    for item in data.get("jobs", []):
                        job_id = item.get("id")
                        job_url = item.get("absolute_url", f"https://boards.greenhouse.io/{board_token}/jobs/{job_id}")
                        clean_url, is_valid, _ = URLNormalizerValidator.resolve_and_validate_url(job_url, careers_url)
                        if is_valid:
                            discovered.append({
                                "company": company_name,
                                "board_token": board_token,
                                "ats_provider": "greenhouse",
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
        board_token = discovery_item.get("board_token")
        company_name = discovery_item.get("company")
        source_url = discovery_item.get("source_url")

        title = raw.get("title", "").strip()
        if not title:
            return None

        job_id = raw.get("id")
        location = raw.get("location", {}).get("name", "Remote")
        departments = [d.get("name") for d in raw.get("departments", []) if d.get("name")]
        dept = departments[0] if departments else None
        content = raw.get("content", "").strip()

        # Canonical Apply URL
        external_apply_url = f"{job_url}#app" if job_url and job_url != "#" else None

        return {
            "external_job_id": f"gh-{board_token}-{job_id}",
            "title": title,
            "company": company_name,
            "department": dept,
            "location": location,
            "remote_type": "Remote" if "remote" in location.lower() else "Hybrid",
            "employment_type": "Full-time",
            "experience_level": None, # Resolved by Normalizer from structured fields / text
            "job_url": job_url,
            "source_url": source_url,
            "external_apply_url": external_apply_url,
            "salary": None, # Zero fabrication policy
            "description": content or None,
            "source": self.name,
            "source_type": self.source_type
        }

    async def fetch(self) -> List[Dict[str, Any]]:
        # Fetching is orchestrated via registry & company lookup
        return []
