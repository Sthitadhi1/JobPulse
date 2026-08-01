<div align="center">

# 🚀 JobPulse

### The Open-Source Intelligent Job Discovery Platform

*Monitor hundreds of company career pages, ATS platforms, and job boards in real-time to discover newly posted technical opportunities.*

![GitHub stars](https://img.shields.io/github/stars/Sthitadhi1/JobPulse?style=for-the-badge&color=gold)
![GitHub forks](https://img.shields.io/github/forks/Sthitadhi1/JobPulse?style=for-the-badge&color=blue)
![GitHub issues](https://img.shields.io/github/issues/Sthitadhi1/JobPulse?style=for-the-badge&color=red)
![Python](https://img.shields.io/badge/Python-3.12+-blue?style=for-the-badge&logo=python)
![FastAPI](https://img.shields.io/badge/FastAPI-Backend-009688?style=for-the-badge&logo=fastapi)
![React](https://img.shields.io/badge/React-Frontend-61DAFB?style=for-the-badge&logo=react)
![TypeScript](https://img.shields.io/badge/TypeScript-5.8-blue?style=for-the-badge&logo=typescript)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-Database-336791?style=for-the-badge&logo=postgresql)
![Docker](https://img.shields.io/badge/Docker-Containerized-2496ED?style=for-the-badge&logo=docker)
![License](https://img.shields.io/badge/License-MIT-yellow.svg?style=for-the-badge)

**Built to help students, fresh graduates, and professionals discover new technical job opportunities before everyone else.**

</div>

---

# 📊 Project at a Glance

| Metric | Current | Target Scale |
|:-------|:-------:|:------------:|
| 🏢 **Company Registry** | **300+ companies** | 1,000+ companies |
| 🔌 **Supported Sources** | Career Pages, LinkedIn, Naukri, ATS Portals | Unlimited Plugin Connectors |
| ⚙️ **ATS Integrations** | **12+ Platforms** (Greenhouse, Lever, Workday, Ashby, etc.) | 20+ Platforms |
| 🔍 **Search Filters** | **15+ Criteria** | 30+ Criteria |
| 🎯 **Experience Levels** | **14 Categories** (`Internship` ➔ `Fellow`) | Custom Taxonomy |
| 📨 **Notification Channels** | **Telegram** (Live) | Email, Push, Slack, Discord |
| 🗄️ **Database Architecture** | **PostgreSQL** / Async SQLAlchemy | Multi-Region Sharded DB |
| 🧩 **System Design** | **Plugin-Based Connector Framework** | Distributed Worker Mesh |
| 🚀 **Backend** | **FastAPI** (Async AsyncIO Engine) | Production Ready |
| 💻 Frontend | **React + TypeScript / Modern UI** | Production Ready |
| 🐳 Deployment | **Docker Compose & CI/CD** | Kubernetes-Ready |

---

# 🚀 Highlights

- 🏢 **300+ Curated Companies**: Fully populated registry across Product Giants, Indian Unicorns/Startups, and IT Services/Consulting firms.
- 🔌 **12+ ATS & Platform Connectors**: Native support for Greenhouse, Lever, Workday, Ashby, SmartRecruiters, Teamtailor, Recruitee, Jobvite, Oracle Taleo, SAP SuccessFactors, LinkedIn Jobs, and Naukri.
- 🌐 **Direct Career Page Ingestion**: Direct ingestion from employer hiring portals prioritized over stale third-party aggregators.
- 🎯 **Weighted Experience Classification**: Multi-signal classification engine with strict guardrails preventing 1–3 YOE roles from misclassification as Freshers.
- 🟢 **Continuous Job Verification Engine**: Multi-cycle revalidation displaying real-time badges (🟢 Verified Today, 🟡 Verification Pending, 🔴 Removed from Source).
- 🔗 **Smart Apply Link Resolution**: Priority URL fallback (`external_apply_url` ➔ `job_url`) preventing generic career homepage redirects.
- 📊 **Real-Time Analytics Telemetry**: Comprehensive hiring trends, daily fresher postings, top hiring skills, and connector health metrics.
- ⚡ **Zero-Code Company Onboarding**: Configuration-driven JSON/DB registry allowing new companies to be onboarded without code modification.
- 🐳 **Docker & Production Ready**: Fully containerized environment with async SQLAlchemy database migrations and automated test suites.

---

# 📖 Overview

Finding software engineering jobs shouldn't require opening dozens of career pages every day.

**JobPulse** continuously discovers newly published technical roles from company career portals, Applicant Tracking Systems (ATS), and selected job platforms, normalizes them into a unified schema, intelligently classifies experience requirements, and instantly notifies users when relevant opportunities appear.

Unlike traditional job boards, JobPulse is **discovery-first**.

> 💡 **JobPulse discovers jobs—it does NOT auto-apply.** Users remain in complete control of every application.

---

# ✨ Features

## 🔍 Intelligent Job Discovery & Scalable Registry
- Indexes software engineering, AI/ML, Data, DevOps, Cloud, Cybersecurity, and Internship roles.
- Supports **300+ companies** out of the box with an extensible architecture designed to scale to **1000+ companies**.
- Independent connector workers supporting isolated retries, rate limiting, and failure recovery.

## 🎯 Smart Search & Filtering
- Multi-parameter Boolean search (`q`, `location`, `country`, `remote_type`, `experience_level`, `min_salary_lpa`, `company`, `source`, `verification_status`).
- Strict experience filtering guaranteeing that users searching for Freshers receive **only genuine entry-level opportunities**.

## 🧠 Weighted Experience Classification Engine
Normalizes postings into **14 standardized categories**:
- `Internship`
- `Campus Hiring`
- `Fresher`
- `Associate`
- `Mid-Level`
- `Senior`
- `Lead`
- `Staff`
- `Principal`
- `Manager`
- `Director`
- `Vice President`
- `Distinguished Engineer`
- `Fellow`

Uses weighted multi-signal logic:
1. Structured experience data (highest precedence).
2. Title & description NLP keyword extraction.
3. Strict YOE numerical requirements evaluation.

## 🛡️ Persistent Job Tracking & Verification Engine
- Replaces naive immediate deletion with multi-cycle lifecycle tracking (`ACTIVE`, `EXPIRED`, `FILLED`, `REMOVED`, `UNKNOWN`).
- Tracks `first_seen`, `last_seen`, `last_verified`, `verification_count`, `consecutive_missing_count`.
- Requires **3 consecutive missing cycles** before marking a job as `REMOVED`. Network drops or 5xx HTTP errors never remove jobs.

## 🟢 Real-Time Verification Badges & Smart Apply Links
- Displays live status badges on job cards:
  - 🟢 **Verified Today**
  - 🟡 **Verification Pending**
  - 🔴 **Removed from Source**
- Smart URL resolution priority: `external_apply_url` ➔ `job_url` ➔ `source_url`.

## 📢 Real-Time Notifications
- Instant alerts sent via Telegram bot whenever matching jobs are indexed.
- Flexible saved search preferences with custom frequency and keyword alerts.

## 📊 Analytics & Connector Diagnostics Dashboard
- Live dashboard displaying:
  - Freshers jobs today, Internships today, Mid-Level today, Senior today.
  - Jobs verified today & verification success rate %.
  - Top hiring companies, active ATS breakdown, top hiring cities.
  - Connector runtime, health status, and success rates.

---

# 🏗️ System Architecture

```
                 +-----------------------------------+
                 | Company Career Pages & ATS Inputs |
                 +-----------------------------------+
                   (Greenhouse, Workday, Ashby, etc.)
                                 │
                                 ▼
                 +-----------------------------------+
                 |     Plugin Connector Engine       |
                 +-----------------------------------+
                                 │
                                 ▼
                 +-----------------------------------+
                 |    URL & Schema Normalization     |
                 +-----------------------------------+
                                 │
                                 ▼
                 +-----------------------------------+
                 |  Weighted Experience Classifier   |
                 +-----------------------------------+
                                 │
                                 ▼
                 +-----------------------------------+
                 |   4-Tier Priority Deduplication   |
                 +-----------------------------------+
                                 │
                                 ▼
                 +-----------------------------------+
                 |  PostgreSQL / Async DB Engine     |
                 +-----------------------------------+
                        │                     │
                        ▼                     ▼
             +---------------------+  +----------------------+
             | Verification Engine |  | Notification Engine  |
             +---------------------+  +----------------------+
                        │                     │
                        └──────────┬──────────┘
                                   ▼
                 +-----------------------------------+
                 |   Dashboard UI & Telemetry API    |
                 +-----------------------------------+
```

---

# ⚡ Tech Stack

### Frontend
- **Framework**: React / Modern Vanilla Web Components & Vite
- **Styling**: Modern CSS Design System (Glassmorphism, Dark Mode tokens, Responsive Grid)
- **State & Routing**: Asynchronous Fetch API & Custom Event Bus

### Backend
- **Framework**: FastAPI (Python 3.12+)
- **ORM & Database**: SQLAlchemy (AsyncIO) & SQLite / PostgreSQL
- **Migrations**: Alembic / Automatic PRAGMA Schema Migrator
- **Task Scheduling**: Custom Async Scheduler & Verification Loop

### Infrastructure & Security
- **Containerization**: Docker & Docker Compose
- **Alert Dispatch**: Telegram Bot API / MarkdownV2 Formatter
- **Testing**: pytest & unittest

---

# 🧠 Core Engineering Concepts

### 🧩 Plugin-Based Connector Architecture
Connectors inherit from a `BaseConnector` class with isolated `initialize()`, `fetch()`, `validate()`, and `shutdown()` methods. New career sources or ATS integrations can be added by declaring a class without altering core scheduler logic.

### 🔍 4-Tier Fingerprint Deduplication
Prevent duplicate job listings using a priority fallback hierarchy:
1. `External Job ID` + `Company`
2. `Canonical URL`
3. `Company` + `Title`
4. `Company` + `Title` + `Location`

### 🛡️ Resilience & Fault Tolerance
Connectors run independently with isolated error handling. Failed connector HTTP requests do not interrupt other connectors, and database schema updates run with zero-downtime column migrations.

---

# 📂 Project Structure

```text
JobPulse/
├── backend/
│   ├── app/
│   │   ├── api/             # FastAPI endpoints (jobs, connectors, analytics, notifications, searches)
│   │   ├── connectors/      # Plugin connector implementations (Greenhouse, Lever, TechCareers, Configurable)
│   │   │   └── config/      # companies.json (300+ Company Registry)
│   │   ├── engine/          # Core engines (normalizer, deduplicator, verification, scheduler, search, matching)
│   │   ├── models/          # SQLAlchemy async database models (Job, CompanyRegistry, ConnectorHealth, etc.)
│   │   ├── notifications/   # Telegram bot notification dispatcher
│   │   ├── config.py        # Pydantic environment settings
│   │   ├── database.py      # Async database connection and auto-migrator
│   │   └── main.py          # FastAPI application entry point
│├── frontend/
│   ├── css/                 # CSS Design tokens and styles
│   ├── js/                  # Frontend interactive scripts
│   └── index.html           # Main SPA dashboard
├── tests/                   # Engine unit test suite
├── TOP_100_COMPANIES.md               # Top 100 Product Companies Registry
├── TOP_100_INDIAN_STARTUPS.md          # Top 100 Indian Startups Registry
├── TOP_100_IT_SERVICES_AND_CONSULTING.md # Top 100 IT Services Registry
├── Dockerfile               # Production container image
├── docker-compose.yml       # Multi-container orchestration
├── run_dev.py               # Development server runner
└── README.md                # Documentation
```

---

# 🚀 Getting Started

### Prerequisites
- Python 3.12+
- Node.js 18+ (optional for frontend assets)
- Docker & Docker Compose (optional)

### Local Setup

1. **Clone the Repository**
   ```bash
   git clone https://github.com/Sthitadhi1/JobPulse.git
   cd JobPulse
   ```

2. **Configure Environment Variables**
   Create a `.env` file in the project root:
   ```env
   TELEGRAM_BOT_TOKEN="your_telegram_bot_token_here"
   DATABASE_URL="sqlite+aiosqlite:///./jobpulse.db"
   ```

3. **Run the Backend Application**
   ```bash
   pip install -r requirements.txt
   python run_dev.py
   ```
   The backend FastAPI server will start at `http://localhost:8000`.

4. **Access the Dashboard**
   Open `http://localhost:8000` in your web browser.

---

# 🐳 Docker Deployment

To spin up JobPulse using Docker Compose:

```bash
docker-compose up -d --build
```

Access the live containerized application at `http://localhost:8000`.

---

# 🗺️ Roadmap

- [x] Project Architecture & Database Schema
- [x] Plugin Connector Framework
- [x] 300+ Company Registry (`companies.json`)
- [x] Weighted Experience Classification Engine (14 categories)
- [x] Persistent Job Tracking & Verification Engine
- [x] Real-time Verification Badges & Smart Apply Links
- [x] Search & Boolean Query Engine
- [x] Telegram Alert Dispatcher
- [x] Real-Time Telemetry & Analytics Dashboard
- [ ] Email Notification Channel
- [ ] Browser Push Notifications
- [ ] Slack & Discord Webhook Connectors
- [ ] AI-Powered Resume-to-Job Matching

---

# 🤝 Contributing

Contributions are warmly welcome! Whether you are adding new company connectors, expanding ATS support, improving classification rules, or refining the UI:

1. Fork the Repository.
2. Create a Feature Branch (`git checkout -b feature/NewConnector`).
3. Commit your changes (`git commit -m 'Add NewConnector'`).
4. Push to the Branch (`git push origin feature/NewConnector`).
5. Open a Pull Request.

---

# 📄 License

This project is licensed under the **MIT License** — see the `LICENSE` file for details.

---

# 👨‍💻 Author

**Sthitadhi Maity**  
B.Tech Computer Science Engineering (Software Engineering)  
SRM Institute of Science and Technology  

- **GitHub**: [@Sthitadhi1](https://github.com/Sthitadhi1)
- **Project Repository**: [JobPulse on GitHub](https://github.com/Sthitadhi1/JobPulse)

---

<div align="center">
⭐ <b>If you find JobPulse helpful, please consider giving it a star on GitHub!</b> ⭐
</div>
