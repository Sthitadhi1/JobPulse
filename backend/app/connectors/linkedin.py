import re
import asyncio
import httpx
from typing import List, Dict, Any, Optional
from urllib.parse import quote
from backend.app.connectors.base import BaseConnector
from backend.app.engine.normalizer import URLNormalizerValidator
from backend.app.engine.dead_link import DeadLinkValidator
from backend.app.models.search_request import SearchRequest

class LinkedInConnector(BaseConnector):
    name: str = "LinkedIn Jobs"
    source_type: str = "Job Board"
    version: str = "3.0.0"

    async def stage1_discover(self, company: Dict[str, Any]) -> List[Dict[str, Any]]:
        return []

    async def stage2_extract(self, discovery_item: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        return None

    async def fetch(self) -> List[Dict[str, Any]]:
        default_req = SearchRequest(keyword="Software Engineer", location="India", page=1)
        return await self.fetch_user_search(default_req)

    async def fetch_user_search(self, request: SearchRequest) -> List[Dict[str, Any]]:
        """
        PART 1, 2 & 3 — User-Driven LinkedIn Search Engine with Concurrent Live Dead-Link Filtering
        Constructs LinkedIn Guest API requests dynamically from user-supplied SearchRequest.
        Validates extracted URLs concurrently with async HEAD/GET checks.
        """
        keyword = (request.keyword or "Software Engineer").strip()
        location = (request.location or "India").strip()
        start = max(0, (request.page - 1) * 25)

        encoded_kw = quote(keyword)
        encoded_loc = quote(location)
        api_url = f"https://www.linkedin.com/jobs-guest/jobs/api/seeMoreJobPostings/search?keywords={encoded_kw}&location={encoded_loc}&start={start}"
        source_url = "https://www.linkedin.com/jobs/search"

        jobs = []
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5"
        }

        try:
            async with httpx.AsyncClient(timeout=4.0, headers=headers, follow_redirects=True) as client:
                res = await client.get(api_url)
                if res.status_code == 200:
                    titles = re.findall(r'<h3 class="base-search-card__title">\s*(.*?)\s*</h3>', res.text, re.DOTALL)
                    companies = re.findall(r'<h4 class="base-search-card__subtitle">\s*<a.*?>\s*(.*?)\s*</a>', res.text, re.DOTALL)
                    locations = re.findall(r'<span class="job-search-card__location">\s*(.*?)\s*</span>', res.text, re.DOTALL)
                    links = re.findall(r'<a class="base-card__full-link.*?" href="(.*?)"', res.text)

                    candidate_jobs = []
                    for i in range(min(len(titles), len(companies), len(locations))):
                        title = titles[i].strip()
                        comp = companies[i].strip()
                        loc = locations[i].strip()
                        raw_link = links[i] if i < len(links) else f"https://www.linkedin.com/jobs/view/{hash(title + comp)}"
                        
                        clean_url, is_valid, _ = URLNormalizerValidator.resolve_and_validate_url(raw_link, source_url)

                        if is_valid:
                            candidate_jobs.append({
                                "external_job_id": f"li-{hash(title + comp)}",
                                "title": title,
                                "company": comp,
                                "location": loc,
                                "remote_type": "Remote" if "remote" in loc.lower() else ("Hybrid" if "hybrid" in loc.lower() else "On-site"),
                                "employment_type": request.employment_type or "Full-time",
                                "job_url": clean_url,
                                "source_url": source_url,
                                "external_apply_url": clean_url,
                                "salary": None, # PART 8: Zero fabrication
                                "description": f"Live LinkedIn position for {title} at {comp} ({loc})",
                                "source": self.name,
                                "source_type": self.source_type
                            })

                    # Run dead-link validation concurrently across candidates
                    async def validate_candidate(job):
                        is_alive, _ = await DeadLinkValidator.validate_url_alive(job["job_url"], timeout_seconds=1.5)
                        return job if is_alive else None

                    val_results = await asyncio.gather(*[validate_candidate(j) for j in candidate_jobs], return_exceptions=True)
                    for r in val_results:
                        if isinstance(r, dict):
                            jobs.append(r)
        except Exception as e:
            print(f"[LinkedInConnector] User search error: {e}")

        return jobs
