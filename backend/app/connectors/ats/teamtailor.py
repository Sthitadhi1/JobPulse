import httpx
from typing import List, Dict, Any, Optional
from backend.app.connectors.base import BaseConnector
from backend.app.engine.normalizer import URLNormalizerValidator

class TeamtailorATSConnector(BaseConnector):
    name: str = "Teamtailor"
    source_type: str = "ATS"
    version: str = "2.0.0"

    async def stage1_discover(self, company: Dict[str, Any]) -> List[Dict[str, Any]]:
        board_token = company.get("board_token") or company.get("id")
        company_name = company.get("name", board_token)
        careers_url = company.get("careers_url", f"https://{board_token}.teamtailor.com")
        discovered = []

        api_url = f"https://{board_token}.teamtailor.com/jobs.json"
        async with httpx.AsyncClient(timeout=6.0, follow_redirects=True) as client:
            try:
                res = await client.get(api_url)
                if res.status_code == 200:
                    data = res.json()
                    for item in data.get("data", []):
                        attrs = item.get("attributes", {})
                        job_id = item.get("id")
                        job_url = attrs.get("url", f"https://{board_token}.teamtailor.com/jobs/{job_id}")
                        clean_url, is_valid, _ = URLNormalizerValidator.resolve_and_validate_url(job_url, careers_url)
                        if is_valid:
                            discovered.append({
                                "company": company_name,
                                "board_token": board_token,
                                "ats_provider": "teamtailor",
                                "job_url": clean_url,
                                "source_url": careers_url,
                                "raw_item": item
                            })
            except Exception:
                pass
        return discovered

    async def stage2_extract(self, discovery_item: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        raw = discovery_item.get("raw_item", {})
        attrs = raw.get("attributes", {})
        job_url = discovery_item.get("job_url")
        company_name = discovery_item.get("company")
        board_token = discovery_item.get("board_token")
        source_url = discovery_item.get("source_url")

        title = attrs.get("title", "").strip()
        if not title:
            return None

        job_id = raw.get("id")
        location = attrs.get("location-name") or "Remote"
        description = attrs.get("body") or attrs.get("pitch")

        external_apply_url = f"{job_url}#apply" if job_url != "#" else None

        return {
            "external_job_id": f"tt-{board_token}-{job_id}",
            "title": title,
            "company": company_name,
            "department": attrs.get("department-name"),
            "location": location,
            "remote_type": "Remote" if attrs.get("remote-status") == "full" or "remote" in location.lower() else "Hybrid",
            "employment_type": attrs.get("employment-type", "Full-time"),
            "experience_level": None,
            "job_url": job_url,
            "source_url": source_url,
            "external_apply_url": external_apply_url,
            "salary": None,
            "description": description or None,
            "source": self.name,
            "source_type": self.source_type
        }

    async def fetch(self) -> List[Dict[str, Any]]:
        return []
