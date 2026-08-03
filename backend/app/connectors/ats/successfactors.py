import httpx
import re
from typing import List, Dict, Any, Optional
from backend.app.connectors.base import BaseConnector
from backend.app.engine.normalizer import URLNormalizerValidator

class SuccessFactorsATSConnector(BaseConnector):
    name: str = "SAP SuccessFactors"
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
                res = await client.get(careers_url)
                if res.status_code == 200:
                    links = re.findall(r'href=["\']([^"\']*(?:job|career|position)[^"\']*)["\']', res.text, re.IGNORECASE)
                    for link in links:
                        clean_url, is_valid, _ = URLNormalizerValidator.resolve_and_validate_url(link, careers_url)
                        if is_valid and clean_url not in [d["job_url"] for d in discovered]:
                            discovered.append({
                                "company": company_name,
                                "board_token": board_token,
                                "ats_provider": "successfactors",
                                "job_url": clean_url,
                                "source_url": careers_url
                            })
            except Exception:
                pass
        return discovered

    async def stage2_extract(self, discovery_item: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        job_url = discovery_item.get("job_url")
        company_name = discovery_item.get("company")
        board_token = discovery_item.get("board_token")
        source_url = discovery_item.get("source_url")

        async with httpx.AsyncClient(timeout=6.0, follow_redirects=True) as client:
            try:
                res = await client.get(job_url)
                if res.status_code == 200:
                    title_match = re.search(r'<h1[^>]*>(.*?)</h1>', res.text, re.IGNORECASE | re.DOTALL)
                    title = re.sub(r'<[^>]+>', '', title_match.group(1)).strip() if title_match else None
                    if not title or len(title) < 3:
                        return None

                    return {
                        "external_job_id": f"sf-{board_token}-{hash(job_url)}",
                        "title": title,
                        "company": company_name,
                        "department": None,
                        "location": "India / Remote",
                        "remote_type": "Hybrid",
                        "employment_type": "Full-time",
                        "experience_level": None,
                        "job_url": job_url,
                        "source_url": source_url,
                        "external_apply_url": job_url,
                        "salary": None,
                        "description": f"SuccessFactors job listing for {title} at {company_name}",
                        "source": self.name,
                        "source_type": self.source_type
                    }
            except Exception:
                pass
        return None

    async def fetch(self) -> List[Dict[str, Any]]:
        return []
