<div align="center">

# 🚀 JobPulse

### The Open-Source Intelligent Job Discovery & Career Operating System

*Continuously monitor 300+ company career pages, 12+ ATS platforms, and job sources in real-time. Discover verified tech opportunities, match resumes with AI-driven scoring, and track applications with a Kanban workspace.*

[![Tests](https://img.shields.io/github/actions/workflow/status/Sthitadhi1/JobPulse/tests.yml?branch=master&style=for-the-badge&label=tests)](https://github.com/Sthitadhi1/JobPulse/actions/workflows/tests.yml)
[![GitHub stars](https://img.shields.io/github/stars/Sthitadhi1/JobPulse?style=for-the-badge&color=gold)](https://github.com/Sthitadhi1/JobPulse/stargazers)
[![GitHub forks](https://img.shields.io/github/forks/Sthitadhi1/JobPulse?style=for-the-badge&color=blue)](https://github.com/Sthitadhi1/JobPulse/network)
[![Python](https://img.shields.io/badge/Python-3.11+-blue?style=for-the-badge&logo=python)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-Backend-009688?style=for-the-badge&logo=fastapi)](https://fastapi.tiangolo.com)
[![SQLAlchemy](https://img.shields.io/badge/SQLAlchemy-AsyncIO-red?style=for-the-badge&logo=sqlalchemy)](https://www.sqlalchemy.org/)
[![Docker](https://img.shields.io/badge/Docker-Containerized-2496ED?style=for-the-badge&logo=docker)](https://www.docker.com/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg?style=for-the-badge)](LICENSE)

**Built for students, new graduates, and software engineers to discover genuine technical opportunities before they get crowded.**

[Live Demo](https://jobpulse-2z2f.onrender.com) • [Report Bug](https://github.com/Sthitadhi1/JobPulse/issues) • [Request Feature](https://github.com/Sthitadhi1/JobPulse/issues)

</div>

---

# 📊 Project at a Glance

| Pillar | Current Architecture | Capabilities |
|:-------|:---------------------|:-------------|
| 🏢 **Company Registry** | **300+ Curated Companies** | Product Giants, Indian Unicorns, Global IT & Consulting |
| 🔌 **ATS Integrations** | **12+ Platforms** | Greenhouse, Lever, Workday, Ashby, SmartRecruiters, Teamtailor, Recruitee, Taleo, SuccessFactors, etc. |
| 🧠 **AI Resume Matcher** | **Multi-Section Intelligence** | Extracts Education, 25+ Ranked Skills, Experience & Projects; calculates 7-part weighted match scores |
| 📋 **Application Workspace** | **Kanban Board + CSV Sync** | Drag-and-drop status pipeline (`Saved` ➔ `Applied` ➔ `OA` ➔ `Interview` ➔ `Offer`) |
| 🟢 **Verification Engine** | **Continuous Lifecycle Guard** | Re-verifies career links; badges live vs expired/closed postings; prevents 404 dead links |
| 🔍 **Discovery & Search** | **Multi-Filter Boolean Engine** | Title, Skills, Salary Chips, Remote Mode, 14 Experience Categories |
| 📨 **Alert Dispatcher** | **Telegram Bot Integration** | Automated real-time notifications for custom saved search alerts |
| 🔄 **CI/CD Automation** | **GitHub Actions Crawler** | Automated crawler every 2 hours + 24/7 Render keep-alive health pinger |
| 🐳 **Deployment Ready** | **Containerized Production** | Docker Compose, Render PaaS (`render.yaml`), Uvicorn async backend |

---

# 🚀 Key Features

### 1. 🔍 Direct ATS & Career Portal Ingestion
- Ingests opportunities directly from official employer career portals (Greenhouse, Lever, Ashby, Workday, SmartRecruiters, LinkedIn Jobs, etc.), bypassing stale third-party scrapers.
- **Smart Link Resolution**: Fallback architecture (`external_apply_url` ➔ `job_url` ➔ `career_url`) guarantees users are directed to the exact job requisition rather than generic homepages.

### 2. 🧠 Multi-Section AI Resume Intelligence Engine
- **Universal Multi-Section Parser**: Dynamically extracts candidates' **Education** (Degree, University, Target Graduation Year, GPA), **Top 15–25 Ranked Technical Skills**, **Work Experience & Internships**, and **Project Portfolios** from PDF and DOCX files.
- **Granular 7-Part Weighted Match Scoring**:
  - 🛠️ **Skill Overlap (35%)**: Dynamic keyword matching across 100+ technical frameworks.
  - 💼 **Experience Seniority (20%)**: Matches junior/intern vs mid/senior roles with strict guardrails.
  - 🎯 **Role Domain Fit (15%)**: Categorizes roles (AI/ML, Backend, Full Stack, DevOps, Data).
  - 🎓 **Education Fit (10%)**: Degree level and academic background relevance.
  - 🚀 **Projects Alignment (10%)**: Evaluates project tech stack relevance against job requirements.
  - 📍 **Location / Work Mode (5%)** & 💰 **Salary Range (5%)**.

### 3. 📋 Interactive Application Kanban Workspace
- Visual drag-and-drop Kanban board managing stages: `Saved`, `Applied`, `OA / Test`, `Interview`, `Offer`, `Rejected`.
- Track applications with 1 click directly from the Discovery feed or AI recommendation cards.
- Full CSV Export and Import capabilities for seamless application logging.

### 4. 🛡️ Persistent Job Verification & Closed Job Detection
- Jobs undergo continuous re-verification cycles.
- Badges display real-time status:
  - 🟢 **Verified & Live**
  - 🟡 **Verification Pending**
  - 🔴 **Closed / Removed from Source** (Disables apply buttons and warns applicants).
- Requires 3 consecutive missing cycles before marking jobs as removed, protecting against temporary network blips.

### 5. ⚡ Automated Search Alert Rules & Telegram Notifications
- Define custom alert rules (Keywords, Location, Min Salary LPA, Remote Mode, Telegram Recipient Chat ID).
- Ingested opportunities matching your rules trigger instant Telegram notifications with direct apply links.

### 6. 📊 Real-Time Analytics & Connector Diagnostics
- Live telemetry command center tracking total indexed jobs, fresher opportunities, active ATS platforms, hiring city breakdowns, and individual connector latency/health.

---

# 🏗️ System Architecture

```
                 +-------------------------------------------------------+
                 |       Company Career Portals & ATS Integrations       |
                 | (Greenhouse, Lever, Ashby, Workday, SmartRecruiters)  |
                 +-------------------------------------------------------+
                                             │
                                             ▼
                 +-------------------------------------------------------+
                 |            Plugin-Based Connector Framework           |
                 +-------------------------------------------------------+
                                             │
                                             ▼
                 +-------------------------------------------------------+
                 |             URL Normalizer & Deduplicator             |
                 +-------------------------------------------------------+
                                             │
                                             ▼
                 +-------------------------------------------------------+
                 |       Multi-Signal Experience & Domain Classifier     |
                 +-------------------------------------------------------+
                                             │
                                             ▼
                 +-------------------------------------------------------+
                 |           Async SQLAlchemy / SQLite / Postgres        |
                 +-------------------------------------------------------+
                        │                    │                    │
                        ▼                    ▼                    ▼
             +---------------------+  +-------------+  +--------------------+
             | Verification Engine |  | AI Matcher  |  | Telegram Dispatch  |
             +---------------------+  +-------------+  +--------------------+
                        │                    │                    │
                        └────────────────────┼────────────────────┘
                                             ▼
                 +-------------------------------------------------------+
                 |  Modern Responsive Dashboard & Application Workspace  |
                 +-------------------------------------------------------+
```

---

# ⚡ Tech Stack

- **Backend**: FastAPI (AsyncIO, Python 3.11+), Pydantic v2, Uvicorn
- **Database & ORM**: SQLAlchemy 2.0 (Async), SQLite / PostgreSQL, Alembic
- **Document Parsing & AI**: PyPDF2, ElementTree DOCX XML extractor, NLP Skill Classifier
- **Frontend**: Vanilla JS (ES6+), CSS3 Modern Bento Design System (Dark/Light Mode, Glassmorphism, Micro-animations)
- **Containerization & CI/CD**: Docker, Docker Compose, GitHub Actions Cron Scheduler
- **Alert Channels**: Telegram Bot API / MarkdownV2

---

# 📂 Project Structure

```text
JobPulse/
├── .github/
│   └── workflows/
│       ├── job_discovery_pipeline.yml  # Scheduled GitHub Actions crawler (runs every 2 hours)
│       └── render_keep_alive.yml       # 24/7 Keep-Alive pinger preventing free-tier sleep
├── backend/
│   ├── app/
│   │   ├── api/                        # REST API routers (jobs, auth, ai, applications, searches, analytics)
│   │   ├── connectors/                 # ATS & Company connectors (Greenhouse, Lever, Configurable, etc.)
│   │   │   └── config/                 # companies.json (300+ Company Registry)
│   │   ├── engine/                     # Core engines (ai_layer, resume_parser, deduplicator, normalizer, verifier)
│   │   ├── models/                     # SQLAlchemy models (Job, User, CandidateProfile, ApplicationTracker, etc.)
│   │   ├── notifications/              # Telegram alert dispatcher
│   │   ├── services/                   # Authentication & Session services
│   │   ├── config.py                   # App configuration & settings
│   │   ├── database.py                 # Async database session & migration helpers
│   │   └── main.py                     # FastAPI entrypoint & static mounts
│   └── run_worker.py                   # Standalone CLI crawler & verification worker
├── frontend/
│   ├── css/style.css                   # Bento Grid design system & dark mode tokens
│   ├── js/app.js                       # SPA state, auth, resume matcher & Kanban board
│   ├── assets/logo.png                 # Brand assets
│   └── index.html                      # Single-page application interface
├── tests/                              # Unit & integration test suites
├── Dockerfile                          # Production container build
├── docker-compose.yml                  # Multi-container orchestration
├── render.yaml                         # PaaS deployment blueprint
├── requirements.txt                    # Production Python dependencies
├── run_dev.py                          # Local development runner
└── README.md                           # Documentation
```

---

# 🚀 Quick Start (Local Setup)

### 1. Clone the Repository
```bash
git clone https://github.com/Sthitadhi1/JobPulse.git
cd JobPulse
```

### 2. Set Up Python Virtual Environment
```bash
python -m venv venv
# On Windows:
.\venv\Scripts\activate
# On Linux / macOS:
source venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Configure Environment Variables (Optional)
Defaults work for local development. To customise, copy the template and edit it:
```bash
cp .env.example .env
```

| Variable | Purpose |
|:--|:--|
| `ADMIN_EMAILS` | Comma-separated emails allowed to post/unlist jobs and trigger crawls |
| `SCHEDULER_SECRET` | Shared secret for cron calls to `/api/v1/admin/connectors/*` (empty = disabled) |
| `SMTP_HOST`, `SMTP_USERNAME`, ... | Email delivery for password-reset codes (without it, codes print to the server log) |
| `TELEGRAM_BOT_TOKEN` | Bot used for saved-search alerts |
| `DATABASE_URL` | SQLite by default; `postgresql+asyncpg://...` for Postgres |

### 5. Launch Development Server
```bash
python run_dev.py
```
Open **`http://localhost:8000/dashboard/`** in your browser. API specifications are accessible at **`http://localhost:8000/docs`**.

### 6. Run the Tests
```bash
python -m unittest discover -s tests -v
```

---

# 🐳 Docker Deployment

To launch JobPulse using Docker Compose:

```bash
docker-compose up -d --build
```
Access the application at `http://localhost:8000`.

---

# 🤖 Background Worker CLI

JobPulse includes a standalone CLI worker for running automated discoveries or verifications:

```bash
# Run a full discovery and verification cycle:
python backend/run_worker.py --mode=all

# Run discovery only:
python backend/run_worker.py --mode=discover

# Run continuous daemon mode (crawls every 2 hours):
python backend/run_worker.py --mode=daemon --interval=7200
```

---

# 🌐 Keeping Render Free Tier Awake 24/7

Render Free web services spin down after 15 minutes of inactivity. To keep your deployment running 24/7 with zero spin-downs:
1. Go to **[UptimeRobot.com](https://uptimerobot.com/)** (Free).
2. Create an **HTTP(s) Monitor**:
   - **URL:** `https://your-app-name.onrender.com/api/v1/health`
   - **Interval:** `Every 5 minutes`
3. Save monitor. The server will receive pings every 5 minutes and remain awake 24/7.

---

# 🔐 Authentication & Security

- **Session Security**: Bearer token + HTTP-only cookie sessions; sessions are rotated on login and password reset.
- **Private Workspaces**: Applications, saved searches, and alert logs are scoped to the signed-in account.
- **Admin-Only Operations**: Posting/unlisting jobs and triggering crawls require an account in `ADMIN_EMAILS` (or the `SCHEDULER_SECRET` for automation).
- **Email OTP Password Reset**: 6-digit codes are delivered by email, expire after `OTP_EXPIRY_MINUTES`, and lock after 5 wrong attempts.
- **No Credential Harvesting**: JobPulse never asks for or stores your credentials for other websites. Most jobs come from employers' public ATS job-board APIs.

Found a vulnerability? Please report it privately; see [SECURITY.md](SECURITY.md).

---

# 🗺️ Roadmap

- [x] Multi-Connector Framework & 300+ Company Registry
- [x] Weighted Multi-Signal Experience Classification Engine
- [x] Continuous Re-verification & Dead-Link Guard
- [x] Multi-Filter Boolean Search & Salary Range Chips
- [x] Multi-Section AI Resume Parser (Education, 25+ Skills, Projects, Experience)
- [x] 7-Part Granular Recommendation & Match Engine
- [x] Application Kanban Tracking Board with CSV Sync
- [x] Automated Search Alert Rules & Telegram Dispatcher
- [x] GitHub Actions Automated Crawler & Render Keep-Alive Workflows
- [ ] Email Notification Channel
- [ ] Browser Push Notifications
- [ ] Discord & Slack Webhook Dispatchers

---

# 🤝 Contributing

Contributions are welcome, and adding a company to the registry is a great first PR.
Read the [Contributing Guide](.github/CONTRIBUTING.md) for setup, tests, and data-source rules,
and the [developer docs](docs/) for how connectors, the scheduler, and verification work.

Please follow the [Code of Conduct](CODE_OF_CONDUCT.md).

---

# 📄 License

Distributed under the **MIT License**. See [`LICENSE`](LICENSE) for more information.

---

# 👨‍💻 Author

**Sthitadhi Maity**  
B.Tech in Computer Science and Engineering (Software Engineering)  
SRM Institute of Science and Technology, Chennai  

- **GitHub**: [@Sthitadhi1](https://github.com/Sthitadhi1)  
- **LinkedIn**: [Sthitadhi Maity](https://linkedin.com/in/sthitadhimaity)  
- **Repository**: [JobPulse on GitHub](https://github.com/Sthitadhi1/JobPulse)

---

<div align="center">
⭐ <b>Star JobPulse on GitHub if you find it helpful!</b> ⭐
</div>
