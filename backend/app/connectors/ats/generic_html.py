import httpx
import re
from typing import List, Dict, Any, Optional
from urllib.parse import urljoin
from backend.app.connectors.base import BaseConnector
from backend.app.engine.normalizer import URLNormalizerValidator

class GenericHTMLATSConnector(BaseConnector):
    name: str = "Generic HTML"
    source_type: str = "Company"
    version: str = "2.0.0"

    async def stage1_discover(self, company: Dict[str, Any]) -> List[Dict[str, Any]]:
        board_token = company.get("board_token") or company.get("id")
        company_name = company.get("name", board_token)
        careers_url = company.get("careers_url", "#")
        discovered = []

        if not careers_url or careers_url == "#":
            return []

        async with httpx.AsyncClient(timeout=6.0, follow_redirects=True, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}) as client:
            try:
                res = await client.get(careers_url)
                if res.status_code == 200:
                    html_text = res.text
                    link_matches = re.findall(r'<a\s+(?:[^>]*?\s+)?href=["\']([^"\']+)["\'][^>]*>(.*?)</a>', html_text, re.IGNORECASE | re.DOTALL)
                    
                    seen_urls = set()
                    for href, raw_text in link_matches:
                        clean_text = re.sub(r'<[^>]+>', '', raw_text).strip()
                        if not clean_text or len(clean_text) < 4:
                            continue
                        
                        abs_url = urljoin(careers_url, href)
                        clean_url, is_valid, _ = URLNormalizerValidator.resolve_and_validate_url(abs_url, careers_url)
                        
                        if clean_url in seen_urls or not is_valid:
                            continue

                        href_lower = href.lower()
                        title_lower = clean_text.lower()

                        is_job_link = any(p in href_lower for p in ["/job/", "/jobs/", "/careers/", "/position/", "/posting/", "/apply/"])
                        is_tech_role = any(k in title_lower for k in ["engineer", "developer", "sde", "software", "backend", "frontend", "fullstack", "data", "ai", "ml", "intern", "trainee"])

                        if is_job_link or is_tech_role:
                            seen_urls.add(clean_url)
                            discovered.append({
                                "company": company_name,
                                "board_token": board_token,
                                "ats_provider": "custom",
                                "job_url": clean_url,
                                "source_url": careers_url,
                                "raw_title": clean_text
                            })
            except Exception:
                pass
        return discovered

    async def stage2_extract(self, discovery_item: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        job_url = discovery_item.get("job_url")
        company_name = discovery_item.get("company")
        board_token = discovery_item.get("board_token")
        source_url = discovery_item.get("source_url")
        raw_title = discovery_item.get("raw_title", "").strip()

        async with httpx.AsyncClient(timeout=6.0, follow_redirects=True, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}) as client:
            try:
                res = await client.get(job_url)
                if res.status_code == 200:
                    title = raw_title
                    title_match = re.search(r'<h1[^>]*>(.*?)</h1>|<title>(.*?)</title>', res.text, re.IGNORECASE | re.DOTALL)
                    if title_match:
                        extracted_t = title_match.group(1) or title_match.group(2)
                        if extracted_t:
                            clean_t = re.sub(r'<[^>]+>', '', extracted_t).strip()
                            if len(clean_t) > 3 and not any(p in clean_t.lower() for p in ["careers", "job openings", "home", "404"]):
                                title = clean_t

                    if not title:
                        return None

                    return {
                        "external_job_id": f"custom-{board_token}-{hash(job_url)}",
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
                        "description": f"Official position for {title} at {company_name}",
                        "source": self.name,
                        "source_type": self.source_type
                    }
            except Exception:
                pass
        return None

    async def fetch(self) -> List[Dict[str, Any]]:
        return []
