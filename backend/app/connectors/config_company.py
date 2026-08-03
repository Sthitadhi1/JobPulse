import os
import json
from typing import List, Dict, Any, Optional
from backend.app.connectors.base import BaseConnector
from backend.app.engine.normalizer import URLNormalizerValidator

CONFIG_FILE_PATH = os.path.join(os.path.dirname(__file__), "config", "companies.json")

class ConfigurableCompanyConnector(BaseConnector):
    """
    Configuration-driven company connector.
    Instantiated dynamically from companies.json without hardcoding mock jobs.
    """
    def __init__(self, company_config: Dict[str, Any]):
        self.company_id = company_config.get("company_id", "company")
        self.name = company_config.get("name", "Company Connector")
        self.category = company_config.get("category", "Company")
        self.ats_type = company_config.get("ats_type", "custom")
        self.career_url = company_config.get("career_url", "#")
        self.source_type = "Company"
        self.version = "2.0.0"
        self.roles = company_config.get("roles") or company_config.get("sample_roles") or []

    async def stage1_discover(self, company: Dict[str, Any]) -> List[Dict[str, Any]]:
        return []

    async def stage2_extract(self, discovery_item: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        return None

    async def fetch(self) -> List[Dict[str, Any]]:
        results = []
        for role in self.roles:
            job_url = role.get("job_url") or role.get("external_apply_url") or self.career_url
            clean_url, is_valid, _ = URLNormalizerValidator.resolve_and_validate_url(job_url, self.career_url)

            if is_valid:
                results.append({
                    "external_job_id": role.get("external_job_id", f"{self.company_id}-{len(results)+1}"),
                    "title": role.get("title", "Software Engineer"),
                    "company": self.name,
                    "location": role.get("location", "India / Remote"),
                    "remote_type": role.get("remote_type", "Hybrid"),
                    "employment_type": role.get("employment_type", "Full-time"),
                    "job_url": clean_url,
                    "source_url": self.career_url,
                    "external_apply_url": role.get("external_apply_url") or clean_url,
                    "salary": role.get("salary"), # None if not provided
                    "description": role.get("description"),
                    "source": f"{self.name} Careers",
                    "source_type": self.source_type
                })
        return results

def load_configurable_company_connectors() -> List[ConfigurableCompanyConnector]:
    connectors = []
    if os.path.exists(CONFIG_FILE_PATH):
        try:
            with open(CONFIG_FILE_PATH, "r", encoding="utf-8") as f:
                configs = json.load(f)
                for cfg in configs:
                    connectors.append(ConfigurableCompanyConnector(cfg))
        except Exception as e:
            print(f"[ConfigurableCompanyConnector] Error loading {CONFIG_FILE_PATH}: {e}")
    return connectors
