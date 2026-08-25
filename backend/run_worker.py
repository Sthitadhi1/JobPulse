"""
JobPulse Standalone CI/CD & Background Automation Worker
=========================================================
Executes automated job discovery, connector ingestion, and dead/ghost-link verification.

Usage:
  python -m backend.run_worker --mode=all        # Runs both discovery and dead-link verification
  python -m backend.run_worker --mode=discover   # Ingests & updates jobs from all connectors
  python -m backend.run_worker --mode=verify     # Verifies all active jobs and prunes dead/404s
  python -m backend.run_worker --mode=daemon     # Continuous background worker loop
"""

import sys
import time
import asyncio
import argparse
import datetime
from sqlalchemy import select

from backend.app.database import init_db, AsyncSessionLocal
from backend.app.models.job import Job
from backend.app.engine.scheduler import scheduler_engine
from backend.app.engine.verification import VerificationEngine

async def run_discovery_task():
    print(f"[{datetime.datetime.utcnow().isoformat()}] [CI/CD] Starting Job Discovery & Connector Ingestion...")
    t0 = time.time()
    async with AsyncSessionLocal() as session:
        result = await scheduler_engine.run_discovery_cycle(session)
        elapsed = round(time.time() - t0, 2)
        print(f"[{datetime.datetime.utcnow().isoformat()}] [CI/CD] Discovery completed in {elapsed}s.")
        print(f"  Status: {result.get('status')}")
        print(f"  Jobs Discovered: {result.get('jobs_discovered', 0)}")
        print(f"  Jobs Inserted: {result.get('jobs_inserted', 0)}")
        print(f"  Jobs Updated: {result.get('jobs_updated', 0)}")
        print(f"  Jobs Removed: {result.get('jobs_removed', 0)}")
        return result

async def run_verification_task(concurrency: int = 30):
    print(f"[{datetime.datetime.utcnow().isoformat()}] [CI/CD] Starting Dead & Ghost Link Verification...")
    t0 = time.time()
    async with AsyncSessionLocal() as session:
        res = await session.execute(select(Job).where(Job.status == "ACTIVE"))
        active_jobs = res.scalars().all()
        total_active = len(active_jobs)
        print(f"  Scanning {total_active} ACTIVE jobs for HTTP 404s, expired postings, and soft-404s...")

        verified_count, removed_count = await VerificationEngine.verify_jobs_batch(
            session, active_jobs, concurrency=concurrency
        )
        elapsed = round(time.time() - t0, 2)
        print(f"[{datetime.datetime.utcnow().isoformat()}] [CI/CD] Verification completed in {elapsed}s.")
        print(f"  Active Verified Live: {verified_count}")
        print(f"  Ghost/Dead Jobs Removed: {removed_count}")
        return {"verified": verified_count, "removed": removed_count, "total_scanned": total_active}

async def run_daemon_loop(interval_seconds: int = 1800, verify_interval_seconds: int = 900):
    print("=" * 65)
    print(f"[JobPulse Daemon] Running continuous automation worker")
    print(f"  Discovery interval: {interval_seconds}s ({interval_seconds // 60} min)")
    print(f"  Verification interval: {verify_interval_seconds}s ({verify_interval_seconds // 60} min)")
    print("=" * 65)

    last_discovery = 0
    last_verification = 0

    while True:
        now = time.time()

        # Run verification pass
        if now - last_verification >= verify_interval_seconds:
            try:
                await run_verification_task()
                last_verification = time.time()
            except Exception as e:
                print(f"[JobPulse Daemon Error] Verification error: {e}")

        # Run discovery pass
        if now - last_discovery >= interval_seconds:
            try:
                await run_discovery_task()
                last_discovery = time.time()
            except Exception as e:
                print(f"[JobPulse Daemon Error] Discovery error: {e}")

        await asyncio.sleep(10)

async def main():
    parser = argparse.ArgumentParser(description="JobPulse CI/CD Automation Worker")
    parser.add_argument(
        "--mode",
        choices=["all", "discover", "verify", "daemon"],
        default="all",
        help="Execution mode (default: all)"
    )
    parser.add_argument(
        "--interval",
        type=int,
        default=1800,
        help="Daemon discovery interval in seconds (default: 1800)"
    )
    parser.add_argument(
        "--concurrency",
        type=int,
        default=30,
        help="Dead link verification concurrency (default: 30)"
    )

    args = parser.parse_args()

    # Ensure DB tables & columns exist
    await init_db()

    if args.mode == "discover":
        await run_discovery_task()
    elif args.mode == "verify":
        await run_verification_task(concurrency=args.concurrency)
    elif args.mode == "all":
        await run_discovery_task()
        await run_verification_task(concurrency=args.concurrency)
    elif args.mode == "daemon":
        await run_daemon_loop(interval_seconds=args.interval)

if __name__ == "__main__":
    asyncio.run(main())
