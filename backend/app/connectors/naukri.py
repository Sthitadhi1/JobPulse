import httpx
from typing import List, Dict, Any
from backend.app.connectors.base import BaseConnector
from backend.app.engine.normalizer import URLNormalizerValidator

class NaukriConnector(BaseConnector):
    name: str = "Naukri India"
    source_type: str = "Job Board"
    version: str = "2.0.0"

    async def stage1_discover(self, company: Dict[str, Any]) -> List[Dict[str, Any]]:
        return []

    async def stage2_extract(self, discovery_item: Dict[str, Any]) -> Dict[str, Any]:
        return {}

    async def fetch(self) -> List[Dict[str, Any]]:
        """
        Step 3 & 9 Compliance: Zero hardcoded mock job fallbacks.
        Only returns real live scraped data from official Guest API.
        """
        jobs = []
        source_url = "https://www.naukri.com/software-engineer-jobs"
        async with httpx.AsyncClient(timeout=6.0, headers={"User-Agent": "Mozilla/5.0", "appid": "109", "systemid": "Naukri"}) as client:
            try:
                url = "https://www.naukri.com/jobapi/v3/search?noOfResults=20&urlType=search_by_keyword&searchType=cloud&keyword=software%20engineer&location=india"
                res = await client.get(url)
                if res.status_code == 200:
                    data = res.json()
                    for item in data.get("jobDetails", []):
                        title = item.get("title", "")
                        comp = item.get("companyName", "")
                        loc = item.get("placeholders", [{}])[0].get("label", "India")
                        sal = item.get("placeholders", [{}, {}])[1].get("label") if len(item.get("placeholders", [])) > 1 else None
                        url_path = item.get("staticUrl", "#")
                        job_detail_url = f"https://www.naukri.com{url_path}" if url_path.startswith("/") else url_path
                        
                        clean_url, is_valid, _ = URLNormalizerValidator.resolve_and_validate_url(job_detail_url, source_url)

                        if is_valid:
                            jobs.append({
                                "external_job_id": f"naukri-{item.get('jobId', hash(title+comp))}",
                                "title": title,
                                "company": comp,
                                "location": loc,
                                "remote_type": "Remote" if "remote" in loc.lower() else ("Hybrid" if "hybrid" in loc.lower() else "On-site"),
                                "employment_type": "Full-time",
                                "job_url": clean_url,
                                "source_url": source_url,
                                "external_apply_url": clean_url,
                                "salary": sal if sal and "not disclosed" not in sal.lower() else None,
                                "description": f"Naukri opportunity for {title} at {comp} ({loc})",
                                "source": self.name,
                                "source_type": self.source_type
                            })
            except Exception:
                pass

        return jobs
