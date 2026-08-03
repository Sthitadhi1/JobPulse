import httpx
from typing import List, Dict, Any, Optional
from backend.app.connectors.base import BaseConnector
from backend.app.engine.normalizer import URLNormalizerValidator

class WorkdayATSConnector(BaseConnector):
    name: str = "Workday"
    source_type: str = "ATS"
    version: str = "2.0.0"

    async def stage1_discover(self, company: Dict[str, Any]) -> List[Dict[str, Any]]:
        board_token = company.get("board_token") or company.get("id")
        company_name = company.get("name", board_token)
        careers_url = company.get("careers_url", "#")
        discovered = []

        if careers_url == "#":
            return []

        async with httpx.AsyncClient(timeout=6.0, follow_redirects=True) as client:
            try:
                # Workday REST API listing endpoint format: https://<domain>/wday/cxs/<tenant>/<site>/jobs
                if "myworkdayjobs.com" in careers_url:
                    # Extract tenant and site from careers_url e.g. https://nvidia.wd5.myworkdayjobs.com/NVIDIAExternalCareerSite
                    parts = careers_url.rstrip("/").split("/")
                    site_name = parts[-1]
                    domain = parts[2] # e.g. nvidia.wd5.myworkdayjobs.com
                    tenant = domain.split(".")[0]

                    api_url = f"https://{domain}/wday/cxs/{tenant}/{site_name}/jobs"
                    payload = {"appliedFacets": {}, "limit": 20, "offset": 0, "searchText": ""}
                    headers = {"Content-Type": "application/json", "Accept": "application/json"}
                    
                    res = await client.post(api_url, json=payload, headers=headers)
                    if res.status_code == 200:
                        data = res.json()
                        for item in data.get("jobPostings", []):
                            external_path = item.get("externalPath", "")
                            job_url = f"https://{domain}{external_path}" if external_path else careers_url
                            clean_url, is_valid, _ = URLNormalizerValidator.resolve_and_validate_url(job_url, careers_url)
                            if is_valid:
                                discovered.append({
                                    "company": company_name,
                                    "board_token": board_token,
                                    "ats_provider": "workday",
                                    "job_url": clean_url,
                                    "source_url": careers_url,
                                    "raw_item": item,
                                    "domain": domain,
                                    "tenant": tenant,
                                    "site_name": site_name
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

        job_req_id = raw.get("bulletFields", [None])[0] or raw.get("jobPostingId") or hash(job_url)
        location = raw.get("locationsText", "India / Remote")
        posted_on = raw.get("postedOn")

        return {
            "external_job_id": f"wd-{board_token}-{job_req_id}",
            "title": title,
            "company": company_name,
            "department": None,
            "location": location,
            "remote_type": "Remote" if "remote" in location.lower() else "Hybrid",
            "employment_type": "Full-time",
            "experience_level": None,
            "job_url": job_url,
            "source_url": source_url,
            "external_apply_url": f"{job_url}/apply" if job_url != "#" else None,
            "salary": None,
            "description": f"Workday posting for {title} at {company_name}. Posted: {posted_on or 'Recently'}",
            "source": self.name,
            "source_type": self.source_type
        }

    async def fetch(self) -> List[Dict[str, Any]]:
        return []
