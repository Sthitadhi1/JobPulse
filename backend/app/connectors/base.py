import datetime
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional

class BaseConnector(ABC):
    name: str = "BaseConnector"
    source_type: str = "ATS"
    version: str = "1.0.0"
    maintainer: str = "JobPulse Core Team"

    async def initialize(self) -> bool:
        """Initialize HTTP client sessions or configurations."""
        return True

    @abstractmethod
    async def fetch(self) -> List[Dict[str, Any]]:
        """Fetch raw public job listings."""
        pass

    def parse(self, raw_data: Any) -> List[Dict[str, Any]]:
        """Parse raw response data into dictionaries."""
        if isinstance(raw_data, list):
            return raw_data
        return []

    def validate(self, job_dict: Dict[str, Any]) -> bool:
        """Validate required schema fields before normalization."""
        required = ["title", "company", "location", "url"]
        for field in required:
            if not job_dict.get(field):
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
