import os
import json
import asyncio
import httpx
from typing import List, Dict, Any, Optional
from backend.app.connectors.base import BaseConnector
from backend.app.engine.normalizer import URLNormalizerValidator
from backend.app.connectors.ats import (
    GreenhouseATSConnector,
    LeverATSConnector,
    WorkdayATSConnector,
    AshbyATSConnector,
    SmartRecruitersATSConnector,
    TeamtailorATSConnector,
    SuccessFactorsATSConnector,
    OracleTaleoATSConnector,
    RecruiteeATSConnector,
    JobviteATSConnector,
    GenericHTMLATSConnector
)

REGISTRY_FILE_PATH = os.path.join(os.path.dirname(__file__), "config", "company_registry.json")

class TwoStageJobIngestionPipeline(BaseConnector):
    name: str = "Two-Stage Ingestion Engine"
    source_type: str = "Company"
    version: str = "4.0.0"

    def __init__(self):
        self.companies = self._load_company_registry()
        self.ats_map = {
            "greenhouse": GreenhouseATSConnector(),
            "lever": LeverATSConnector(),
            "workday": WorkdayATSConnector(),
            "ashby": AshbyATSConnector(),
            "smartrecruiters": SmartRecruitersATSConnector(),
            "teamtailor": TeamtailorATSConnector(),
            "successfactors": SuccessFactorsATSConnector(),
            "sap": SuccessFactorsATSConnector(),
            "oracle_taleo": OracleTaleoATSConnector(),
            "taleo": OracleTaleoATSConnector(),
            "recruitee": RecruiteeATSConnector(),
            "jobvite": JobviteATSConnector(),
            "custom": GenericHTMLATSConnector(),
            "html": GenericHTMLATSConnector()
        }

    def _load_company_registry(self) -> List[Dict[str, Any]]:
        if os.path.exists(REGISTRY_FILE_PATH):
            try:
                with open(REGISTRY_FILE_PATH, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    return [c for c in data if c.get("enabled", True)]
            except Exception as e:
                print(f"[TwoStageJobIngestionPipeline] Error loading registry: {e}")
        return []

    async def stage1_discover(self, company: Dict[str, Any]) -> List[Dict[str, Any]]:
        ats_type = company.get("ats_provider", "custom").lower()
        connector = self.ats_map.get(ats_type, self.ats_map["custom"])
        return await connector.stage1_discover(company)

    async def stage2_extract(self, discovery_item: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        ats_type = discovery_item.get("ats_provider", "custom").lower()
        connector = self.ats_map.get(ats_type, self.ats_map["custom"])
        return await connector.stage2_extract(discovery_item)

    async def fetch(self) -> List[Dict[str, Any]]:
        """
        True Two-Stage Crawling (Step 4 & 5):
        Stage 1: Discover individual job URLs across Company Registry into queue (Do NOT normalize yet)
        Stage 2: Extract individual job page details (Title, Description, Department, Experience, Employment Type, Location, Remote, Salary, Requirements, Canonical Apply URL)
        """
        if not self.companies:
            return []

        # Stage 1: Parallel Discovery
        discovery_tasks = [self.stage1_discover(c) for c in self.companies]
        discovery_results = await asyncio.gather(*discovery_tasks, return_exceptions=True)

        discovery_queue = []
        for res in discovery_results:
            if isinstance(res, list):
                discovery_queue.extend(res)

        # Stage 2: Parallel Extraction
        extraction_tasks = [self.stage2_extract(item) for item in discovery_queue]
        extraction_results = await asyncio.gather(*extraction_tasks, return_exceptions=True)

        extracted_jobs = []
        for job in extraction_results:
            if isinstance(job, dict) and job.get("title"):
                extracted_jobs.append(job)

        return extracted_jobs

# Alias for backward compatibility
TechCareersConnector = TwoStageJobIngestionPipeline
