import time
import datetime
from typing import List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func

from backend.app.connectors.base import BaseConnector
from backend.app.connectors.greenhouse import GreenhouseConnector
from backend.app.connectors.lever import LeverConnector
from backend.app.connectors.tech_careers import TechCareersConnector
from backend.app.connectors.linkedin import LinkedInConnector
from backend.app.connectors.naukri import NaukriConnector
from backend.app.connectors.config_company import load_configurable_company_connectors
from backend.app.models.job import ConnectorHealth, ConnectorExecution

class ConnectorRegistry:
    def __init__(self):
        self._connectors: List[BaseConnector] = [
            GreenhouseConnector(),
            LeverConnector(),
            TechCareersConnector(),
            LinkedInConnector(),
            NaukriConnector()
        ]
        # Automatically load configuration-driven company connectors
        configurable_connectors = load_configurable_company_connectors()
        self._connectors.extend(configurable_connectors)

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

    async def run_single_connector(self, connector: BaseConnector, db: AsyncSession) -> Dict[str, Any]:
        """
        PART 5 — Accurate Runtime & Metric Measurement Pipeline
        started_at -> fetch -> normalize -> deduplicate -> save -> finished_at
        """
        started_at = datetime.datetime.utcnow()
        t0 = time.time()
        
        jobs_discovered = 0
        jobs_inserted = 0
        jobs_updated = 0
        jobs_skipped = 0
        errors_count = 0
        error_msg = None
        status = "SUCCESS"
        valid_jobs = []

        try:
            await connector.initialize()
            raw_jobs = await connector.fetch()
            valid_jobs = [j for j in raw_jobs if connector.validate(j)]
            jobs_discovered = len(raw_jobs)
            jobs_skipped = len(raw_jobs) - len(valid_jobs)
        except Exception as e:
            status = "FAILED"
            errors_count += 1
            error_msg = str(e)
        finally:
            await connector.shutdown()

        finished_at = datetime.datetime.utcnow()
        duration_ms = round((time.time() - t0) * 1000.0, 2)

        # Log exact execution into ConnectorExecution table
        execution = ConnectorExecution(
            connector_name=connector.name,
            source_type=connector.source_type,
            started_at=started_at,
            finished_at=finished_at,
            duration_ms=duration_ms,
            jobs_discovered=jobs_discovered,
            jobs_inserted=jobs_inserted, # Updated by scheduler pipeline
            jobs_updated=jobs_updated,
            jobs_skipped=jobs_skipped,
            errors_count=errors_count,
            error_message=error_msg,
            status=status
        )
        db.add(execution)
        await db.commit()

        # Compute dynamic historical rolling average runtime from DB
        avg_res = await db.execute(
            select(func.avg(ConnectorExecution.duration_ms)).where(ConnectorExecution.connector_name == connector.name)
        )
        avg_runtime_ms = round(avg_res.scalar() or duration_ms, 2)

        # Update ConnectorHealth dashboard record
        health_res = await db.execute(select(ConnectorHealth).where(ConnectorHealth.name == connector.name))
        health_record = health_res.scalars().first()

        if not health_record:
            health_record = ConnectorHealth(
                name=connector.name,
                source_type=connector.source_type,
                status="ACTIVE" if status == "SUCCESS" else "ERROR",
                last_run=started_at,
                jobs_found_last_run=len(valid_jobs),
                total_jobs_indexed=len(valid_jobs),
                average_runtime_ms=avg_runtime_ms,
                error_message=error_msg
            )
            db.add(health_record)
        else:
            health_record.status = "ACTIVE" if status == "SUCCESS" else "ERROR"
            health_record.last_run = started_at
            health_record.jobs_found_last_run = len(valid_jobs)
            health_record.total_jobs_indexed += len(valid_jobs)
            health_record.average_runtime_ms = avg_runtime_ms
            health_record.error_message = error_msg

        await db.commit()
        return {
            "connector": connector.name,
            "jobs": valid_jobs,
            "duration_ms": duration_ms,
            "avg_runtime_ms": avg_runtime_ms,
            "status": status,
            "error": error_msg
        }

    async def run_all_connectors(self, db: AsyncSession) -> List[Dict[str, Any]]:
        all_jobs = []
        for connector in self._connectors:
            res = await self.run_single_connector(connector, db)
            all_jobs.extend(res.get("jobs", []))
        return all_jobs

connector_registry = ConnectorRegistry()
