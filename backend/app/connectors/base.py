import datetime
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional

class BaseConnector(ABC):
    name: str = "BaseConnector"
    source_type: str = "ATS"
    version: str = "2.0.0"
    maintainer: str = "JobPulse Core Team"

    async def initialize(self) -> bool:
        """Initialize HTTP client sessions or configurations."""
        return True

    @abstractmethod
    async def stage1_discover(self, company: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Stage 1: Visit company careers portal or board listing API endpoint.
        Extract individual job listing candidate URLs into a discovery queue.
        Do NOT normalize or extract full content yet.
        """
        pass

    @abstractmethod
    async def stage2_extract(self, discovery_item: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Stage 2: Visit each individual job page or fetch job detail API.
        Extract Title, Description, Department, Experience, Employment Type, Location, Remote Status, Salary, Requirements, Skills, Posting Date, Canonical Apply URL.
        Returns raw extracted data dict or None if invalid.
        """
        pass

    @abstractmethod
    async def fetch(self) -> List[Dict[str, Any]]:
        """Run full two-stage discovery and extraction across configured sources."""
        pass

    def parse(self, raw_data: Any) -> List[Dict[str, Any]]:
        """Parse raw response data into dictionaries."""
        if isinstance(raw_data, list):
            return raw_data
        return []

    def validate(self, job_dict: Dict[str, Any]) -> bool:
        """Validate required schema fields before normalization."""
        if not job_dict:
            return False
        if not job_dict.get("title") or not job_dict.get("company"):
            return False
        job_link = job_dict.get("job_url") or job_dict.get("url") or job_dict.get("apply_url")
        if not job_link or job_link == "#":
            return False
        return True

    async def health_check(self) -> Dict[str, Any]:
        """Expose connector health diagnostics."""
        return {
            "name": self.name,
            "source_type": self.source_type,
            "version": self.version,
            "status": "HEALTHY",
            "timestamp": datetime.datetime.utcnow().isoformat()
        }

    async def shutdown(self) -> None:
        """Cleanup network connections."""
        pass
