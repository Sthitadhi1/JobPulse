import time
import datetime
from typing import List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from backend.app.connectors.base import BaseConnector
from backend.app.connectors.greenhouse import GreenhouseConnector
from backend.app.connectors.lever import LeverConnector
from backend.app.connectors.tech_careers import TechCareersConnector
from backend.app.models.job import ConnectorHealth

class ConnectorRegistry:
    def __init__(self):
        self._connectors: List[BaseConnector] = [
            GreenhouseConnector(),
            LeverConnector(),
            TechCareersConnector()
        ]

    def register_connector(self, connector: BaseConnector):
        self._connectors.append(connector)

    def list_connectors(self) -> List[Dict[str, str]]:
        return [
            {
                "name": c.name,
                "source_type": c.source_type,
                "version": c.version
            }
            for c in self._connectors
        ]

    async def run_all_connectors(self, db: AsyncSession) -> List[Dict[str, Any]]:
        all_jobs = []

        for connector in self._connectors:
            start_time = datetime.datetime.utcnow()
            t0 = time.time()
            jobs_found = 0
            status = "ACTIVE"
            error_msg = None

            try:
                await connector.initialize()
                raw_jobs = await connector.fetch()
                valid_jobs = [j for j in raw_jobs if connector.validate(j)]
                jobs_found = len(valid_jobs)
                all_jobs.extend(valid_jobs)
            except Exception as e:
                status = "ERROR"
                error_msg = str(e)
            finally:
                await connector.shutdown()

            runtime_ms = round((time.time() - t0) * 1000, 2)

            result = await db.execute(select(ConnectorHealth).where(ConnectorHealth.name == connector.name))
            health_record = result.scalars().first()

            if not health_record:
                health_record = ConnectorHealth(
                    name=connector.name,
                    source_type=connector.source_type,
                    status=status,
                    last_run=start_time,
                    jobs_found_last_run=jobs_found,
                    total_jobs_indexed=jobs_found,
                    average_runtime_ms=runtime_ms,
                    error_message=error_msg
                )
                db.add(health_record)
            else:
                health_record.status = status
                health_record.last_run = start_time
                health_record.jobs_found_last_run = jobs_found
                health_record.total_jobs_indexed += jobs_found
                health_record.average_runtime_ms = runtime_ms
                health_record.error_message = error_msg

        await db.commit()
        return all_jobs

connector_registry = ConnectorRegistry()
