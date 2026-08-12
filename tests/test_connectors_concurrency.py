import unittest
import asyncio
from typing import List, Dict, Any
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy import select

from backend.app.database import Base
from backend.app.connectors.base import BaseConnector
from backend.app.connectors.registry import ConnectorRegistry
from backend.app.models.job import ConnectorExecution, ConnectorHealth

class MockSuccessConnector(BaseConnector):
    name = "MockSuccess"
    source_type = "Mock"

    async def initialize(self) -> bool:
        return True

    async def stage1_discover(self, company: Dict[str, Any]) -> List[Dict[str, Any]]:
        return []

    async def stage2_extract(self, discovery_item: Dict[str, Any]):
        return None

    async def fetch(self) -> List[Dict[str, Any]]:
        await asyncio.sleep(0.05)
        return [{
            "title": "Backend SDE",
            "company": "Mock Co",
            "job_url": "https://mock.com/job/1",
            "source": "Mock",
            "location": "Remote"
        }]

    async def shutdown(self) -> None:
        self.shutdown_called = True

class MockFailingConnector(BaseConnector):
    name = "MockFailing"
    source_type = "Mock"

    async def initialize(self) -> bool:
        return True

    async def stage1_discover(self, company: Dict[str, Any]) -> List[Dict[str, Any]]:
        return []

    async def stage2_extract(self, discovery_item: Dict[str, Any]):
        return None

    async def fetch(self) -> List[Dict[str, Any]]:
        await asyncio.sleep(0.05)
        raise RuntimeError("Mock network failure")


    async def shutdown(self) -> None:
        self.shutdown_called = True

class TestConnectorsConcurrency(unittest.TestCase):
    def setUp(self):
        self.engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
        self.AsyncSessionLocal = async_sessionmaker(bind=self.engine, class_=AsyncSession, expire_on_commit=False)

    def tearDown(self):
        asyncio.run(self.engine.dispose())

    def test_run_single_connector_success_and_telemetry(self):
        async def run_check():
            async with self.engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)

            registry = ConnectorRegistry()
            conn_ok = MockSuccessConnector()

            async with self.AsyncSessionLocal() as session:
                res = await registry.run_single_connector(conn_ok, session, execution_id="exec-111")
                self.assertEqual(res["status"], "SUCCESS")
                self.assertEqual(len(res["jobs"]), 1)
                self.assertTrue(getattr(conn_ok, "shutdown_called", False))

                # Check execution record
                exec_res = await session.execute(select(ConnectorExecution).where(ConnectorExecution.connector_name == "MockSuccess"))
                exec_rec = exec_res.scalars().first()
                self.assertIsNotNone(exec_rec)
                self.assertEqual(exec_rec.execution_id, "exec-111")
                self.assertEqual(exec_rec.jobs_discovered, 1)

        asyncio.run(run_check())

    def test_run_single_connector_failure_isolation_and_shutdown(self):
        async def run_check():
            async with self.engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)

            registry = ConnectorRegistry()
            conn_fail = MockFailingConnector()

            async with self.AsyncSessionLocal() as session:
                res = await registry.run_single_connector(conn_fail, session, execution_id="exec-222")
                self.assertEqual(res["status"], "FAILED")
                self.assertIn("Mock network failure", res["error"])
                # Shutdown MUST be called even on fetch failure
                self.assertTrue(getattr(conn_fail, "shutdown_called", False))

                # Check health status
                health_res = await session.execute(select(ConnectorHealth).where(ConnectorHealth.name == "MockFailing"))
                health_rec = health_res.scalars().first()
                self.assertIsNotNone(health_rec)
                self.assertEqual(health_rec.status, "ERROR")

        asyncio.run(run_check())

if __name__ == "__main__":
    unittest.main()
