# JobPulse v2 — Developer Guide

## Quick Start

### 1. Installation
```bash
git clone https://github.com/Sthitadhi1/JobPulse.git
cd JobPulse
pip install -r backend/requirements.txt
```

### 2. Run Dev Server
```bash
python run_dev.py
```

### 3. Run Test Suite
```bash
python -m unittest discover -s tests
```

---

## Codebase Architecture

```
backend/
├── app/
│   ├── api/             # REST endpoints (jobs, connectors, analytics, ai, searches)
│   ├── connectors/      # Connector framework & ATS resolvers
│   │   ├── ats/         # Consolidated ATS Connectors (Greenhouse, Lever, Workday, Ashby, etc.)
│   │   ├── base.py      # BaseConnector abstract class
│   │   ├── registry.py  # Connector Registry & Health Logger
│   │   └── two_stage_crawler.py # TwoStageJobIngestionPipeline
│   ├── engine/          # Core ingestion engines (normalizer, deduplicator, verification, search, ai)
│   ├── models/          # SQLAlchemy database schemas
│   ├── config.py        # Environment settings
│   ├── database.py      # Async SQLite / PostgreSQL session setup
│   └── main.py          # FastAPI application factory
frontend/                # Production frontend (HTML, CSS, JS dashboard)
tests/                   # Automated pytest / unittest test suite
docs/                    # Technical architecture & developer guides
```

---

## Contribution Guidelines

1. **Zero Fabrication**: Never fabricate salary, description, or department fields.
2. **Two-Stage Crawling**: Always separate URL discovery (Stage 1) from detail parsing (Stage 2).
3. **Canonical Apply Links**: Always preserve direct apply links (`external_apply_url` -> `job_url`). Never return homepage URLs.
