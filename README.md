# JobPulse 🚀

**Never Miss Another Job Opportunity.**

JobPulse is an open-source job discovery platform that continuously monitors publicly accessible company career pages and supported Applicant Tracking Systems (ATS) to help students, fresh graduates, and professionals discover newly posted jobs in real time.

Instead of manually checking dozens of career websites every day, users define their preferences once, and JobPulse continuously searches for matching opportunities and sends instant notifications.

> **JobPulse discovers jobs—it does not auto-apply.** Users remain in full control of every application.

---

# Why JobPulse?

Finding jobs is often repetitive and time-consuming.

Candidates repeatedly visit:

* Company career pages
* ATS-powered hiring portals
* Startup hiring boards
* Remote job boards

JobPulse automates the discovery process while respecting the user's decision to review and apply manually.

---

# Core Features — JobPulse V2

### 🔍 Intelligent Job Discovery & 300+ Company Registry

Continuously scans 300+ top product companies, Indian startups/unicorns, IT services, and consulting firms indexed in `companies.json`.

Supports:
* Software Engineers, AI/ML Engineers, Data Engineers, DevOps Engineers, Security Engineers, SREs, Product Engineers, and Interns.
* Configuration-driven Company Registry scalable to 1000+ companies without code changes.

---

### 🧠 Weighted Experience Classification Engine

Normalizes all postings into 14 standardized experience categories:
`Internship` | `Campus Hiring` | `Fresher` | `Associate` | `Mid-Level` | `Senior` | `Lead` | `Staff` | `Principal` | `Manager` | `Director` | `Vice President` | `Distinguished Engineer` | `Fellow`

* **Strict Experience Guardrail**: Roles requiring 1–3 YOE or 2+ YOE are classified as Mid-Level / Associate and **never misclassified as Freshers**.

---

### 🛡️ Persistent Job Tracking & Verification Engine

* **Persistent State Machine**: Tracks job status (`ACTIVE`, `EXPIRED`, `FILLED`, `REMOVED`, `UNKNOWN`) and verification indicators.
* **Multi-Cycle Verification**: Requires 3 consecutive missing cycles before marking a job as `REMOVED`. Network drops never delete active listings.
* **Real-Time Verification Badges**: Displays 🟢 **Verified Today**, 🟡 **Verification Pending**, 🔴 **Removed from Source** badges along with `First Seen` and `Last Verified` timestamps.

---

### 🔗 Smart Apply Links

* Priority resolution target: `external_apply_url` ➔ `job_url`.
* Strictly prevents redirecting users to generic company homepages or career search pages.

---

### 🎯 Smart Multi-Criteria Search & Analytics Dashboard

Filter jobs by:
* Role, Company, Location, Country, Remote Mode (`Remote`, `Hybrid`, `On-site`), Min Salary, ATS Provider, Verification Status, and Posting Date.
* Live Telemetry Dashboard tracking daily fresher postings, internships, verification rates, and top hiring companies.

* Salary (when available)

---

### 📢 Instant Notifications

Receive alerts through:

* Telegram (v1)
* Email (planned)
* Browser Push (planned)
* Slack (planned)
* Discord (planned)

---

### 💾 Saved Searches

Create reusable searches.

Example:

```text
Role: Software Engineer

Location: Bengaluru

Experience: 0–1 Years

Remote: Hybrid + Remote
```

JobPulse automatically monitors these searches.

---

### 📚 Application Tracker

Track your progress manually.

Statuses include:

* Interested
* Applied
* Assessment
* Interview
* Offer
* Rejected
* Accepted

---

### ⭐ Bookmark Jobs

Save interesting opportunities for later review.

---

### 📈 Analytics

Understand:

* Hiring trends
* Active companies
* Popular job titles
* Search history
* Notification activity

---

### 🔌 Plugin-Based Connectors

New job sources can be added without changing the core platform.

---

# Project Goals

JobPulse aims to:

* Help users discover jobs faster.
* Reduce repetitive manual searching.
* Provide a clean, modern experience.
* Encourage community contributions.
* Remain modular and extensible.
* Stay API-first.

---

# Technology Stack

## Frontend

* React
* TypeScript
* Vite
* Tailwind CSS

## Backend

* FastAPI
* Python
* SQLAlchemy
* Pydantic

## Database

* PostgreSQL

## Scheduler

* APScheduler

## Notifications

* Telegram Bot API

## Infrastructure

* Docker
* Docker Compose
* GitHub Actions

---

# Project Structure

```text
JobPulse/

├── backend/
├── frontend/
├── connectors/
├── shared/
├── docs/
├── scripts/
├── docker/
├── tests/
└── .github/
```

---

# Documentation

Detailed documentation is available in the `docs/` directory.

* PROJECT_INTRO.md
* PRD.md
* SYSTEM_DESIGN.md
* DATABASE_DESIGN.md
* API_SPEC.md
* SCRAPER_ENGINE.md
* UI_UX.md
* ROADMAP.md
* CONTRIBUTING.md
* DEPLOYMENT.md
* ARCHITECTURE_DECISIONS.md

---

# Getting Started

## Clone

```bash
git clone https://github.com/<your-username>/JobPulse.git
cd JobPulse
```

---

## Configure

Copy the example environment configuration.

```bash
cp .env.example .env
```

Update the required values before starting the application.

---

## Start Development

The project supports Docker-based development as well as native local setup.

Detailed instructions are available in `DEPLOYMENT.md`.

---

# Roadmap

Current milestone:

* Project Foundation

Upcoming milestones:

* Authentication
* Connector Framework
* Greenhouse Connector
* Lever Connector
* Dashboard
* Telegram Notifications
* Analytics
* Version 1.0

See `ROADMAP.md` for the complete implementation plan.

---

# Contributing

We welcome contributions of all sizes.

You can help by:

* Building connectors
* Improving documentation
* Fixing bugs
* Writing tests
* Enhancing the UI
* Reviewing pull requests

Please read `CONTRIBUTING.md` before submitting changes.

---

# Project Principles

JobPulse is built around the following principles:

* Human-in-the-loop applications
* Publicly accessible job discovery
* Clean architecture
* Modular design
* Accessibility
* Open collaboration
* Documentation-first development

---

# License

This project will be released under the MIT License (or another chosen open-source license).

See the `LICENSE` file for details.

---

# Community

Future community resources may include:

* GitHub Discussions
* Issue Tracker
* Release Notes
* Documentation Website

---

# Status

🚧 **Active Development**

JobPulse is currently under active development.

Core architecture and documentation are complete, and implementation is beginning according to the roadmap.

---

# Vision

Build the best open-source job discovery platform for students, fresh graduates, and professionals.

The long-term vision is to support hundreds of companies, multiple notification channels, a rich plugin ecosystem, and a thriving open-source contributor community while helping users discover relevant opportunities as quickly as possible.
