# PRD.md

# Product Requirements Document

**Project Name:** JobPulse

**Version:** 1.0

**Status:** Draft

**Type:** Open Source Web Platform

**Primary Platform:** Web + Telegram

---

# 1. Product Vision

JobPulse is an open-source, real-time job discovery platform that continuously monitors publicly accessible job sources and company career pages to help students, fresh graduates, and early-career professionals discover new opportunities as soon as they are posted.

The platform is designed around one principle:

> "Users should never have to manually search for jobs every day."

Instead, users create one or more searches describing the positions they want, and JobPulse continuously watches supported sources. Whenever a matching opportunity is discovered, the user receives an immediate notification.

The platform never submits applications on behalf of users. Users remain in complete control of the application process.

---

# 2. Problem Statement

Current job hunting is fragmented.

Students must visit:

* Company career pages
* ATS platforms
* Startup hiring sites
* Job portals
* Remote job boards

every day to avoid missing opportunities.

Many desirable jobs receive hundreds or thousands of applications within hours of being posted.

Current job boards also suffer from:

* Delayed indexing
* Duplicate listings
* Poor filtering
* Outdated jobs
* Irrelevant recommendations
* Manual searching

The result is a time-consuming and inefficient job search process.

---

# 3. Product Goals

## Primary Goals

Build the fastest open-source job discovery platform.

Continuously monitor supported public job sources.

Notify users within minutes of discovering matching jobs.

Require zero manual searching after saved searches are configured.

Maintain a modular architecture that allows contributors to add new sources.

---

## Secondary Goals

Provide a clean and intuitive dashboard.

Support Telegram notifications.

Support email notifications.

Provide powerful filtering.

Become community maintained.

Require no paid APIs.

Be production ready.

---

# 4. Non-Goals

JobPulse will NOT:

* Apply for jobs automatically
* Fill application forms
* Upload resumes
* Generate resumes
* Generate cover letters
* Bypass authentication
* Circumvent CAPTCHAs
* Scrape behind login walls
* Store credentials for third-party job sites
* Violate website terms of service

---

# 5. Target Users

## Primary Audience

* Final-year students
* Fresh graduates
* Campus placement candidates
* Entry-level software engineers

Typical target salary range:

* ₹6 LPA
* ₹8 LPA
* ₹10 LPA
* ₹12 LPA
* ₹15 LPA

---

## Secondary Audience

* Experienced developers
* Career switchers
* Remote job seekers
* International applicants

---

# 6. User Personas

## Persona A

Engineering student.

Searching for:

Software Engineer

Location:

India

Experience:

0–1 years

Notification:

Telegram

---

## Persona B

Backend Developer

Searching:

Backend Engineer

Go Developer

Python Backend

Node.js

Remote only

---

## Persona C

AI Engineer

Searching

Machine Learning Engineer

AI Engineer

LLM Engineer

Generative AI

Python

Remote

---

# 7. User Stories

As a student,

I want to save a search for Software Engineer jobs

so I never need to search again.

---

As a user,

I want to receive a Telegram notification

whenever a new matching job appears.

---

As a user,

I want duplicate listings removed

so I don't waste time.

---

As a user,

I want jobs sorted by newest first.

---

As a user,

I want to bookmark jobs

for later.

---

As a user,

I want to hide companies

I don't wish to apply to.

---

As a user,

I want to filter by location,

experience,

job type,

and posting date.

---

# 8. Functional Requirements

## Authentication

Must support:

* Email/password
* Google OAuth (future)
* GitHub OAuth (future)
* Guest browsing

---

## Dashboard

Display:

Saved searches

Recent jobs

Bookmarks

Notification status

Search analytics

Recent notifications

Application tracker

---

## Job Search

Support searching by:

Job title

Keywords

Location

Experience

Job type

Salary (when available)

Company

Source

Posting date

---

## Search Operators

Support:

AND

OR

NOT

Exact phrase

Examples

Software Engineer AND Backend

Python OR Java

NOT Internship

---

## Saved Searches

Unlimited saved searches.

Each search includes:

Name

Keywords

Locations

Experience

Notification status

Created date

Last matched

---

## Job Feed

Every result must display:

Company

Job title

Location

Remote status

Experience

Employment type

Posting time

Source

Apply URL

Bookmark button

Share button

---

## Sorting

Newest

Oldest

Company

Relevance

Salary (if available)

---

## Filtering

Location

Remote

Hybrid

On-site

Experience

0–1

1–3

3–5

5+

Job Type

Full-time

Internship

Contract

Part-time

Posting Time

Last hour

6 hours

12 hours

24 hours

3 days

7 days

Salary

Minimum

Maximum

Company Include

Company Exclude

---

## Bookmarking

Folders:

Interested

Applied

Interview

Offer

Rejected

Archive

---

## Notification System

Phase 1

Telegram

Phase 2

Email

Phase 3

Browser Push

Discord

Slack

---

## Search History

Maintain previous searches.

Allow re-running with one click.

---

## Company Profiles

Display:

Company name

Website

Industry

Current openings

Past discovered jobs

Hiring frequency

---

## Analytics Dashboard

Display:

Jobs discovered today

Jobs this week

Most active companies

Most active locations

Most common job titles

Most requested searches

Notification delivery success

---

# 9. Supported Job Sources

The platform should use a connector-based architecture.

Initial connector categories:

### ATS Platforms

* Greenhouse
* Lever
* Ashby
* Workday
* SmartRecruiters
* iCIMS
* BambooHR
* Jobvite
* Teamtailor
* Recruitee

---

### Company Career Pages

Initial focus:

Top Product Companies

Top Service Companies

Each company should have an independent connector.

---

### Startup Platforms

* Wellfound
* YC Jobs
* Other publicly accessible startup job sources

---

### Remote Job Platforms

Publicly accessible remote job providers that permit indexing.

---

### Community Connectors

The platform architecture should allow contributors to build additional connectors for supported public sources without modifying the core application.

---

# 10. Notification Requirements

Notifications should include:

Company

Role

Location

Posting time

Source

Direct application link

Notifications should be sent only once per user for each matching job.

---

# 11. Performance Requirements

Search latency:

Under 500 ms for cached searches.

Notification latency:

Target under five minutes from job discovery.

Dashboard load time:

Under two seconds.

System uptime:

99.5% target.

---

# 12. Security Requirements

* HTTPS
* JWT authentication
* Password hashing
* Input validation
* Rate limiting
* CSRF protection
* SQL injection prevention
* XSS prevention
* Secure session handling
* Audit logging

---

# 13. Accessibility

The interface should:

* Be fully keyboard accessible.
* Meet WCAG 2.1 AA guidelines where practical.
* Support dark mode and light mode.
* Be responsive across desktop, tablet, and mobile.

---

# 14. Success Metrics

Technical KPIs

* Average notification latency
* Successful connector execution rate
* Duplicate detection accuracy
* Average search response time
* Platform uptime

Product KPIs

* Registered users
* Daily active users
* Saved searches per user
* Jobs discovered per day
* Notification open rate
* Bookmark rate
* Returning users

Community KPIs

* GitHub stars
* Contributors
* Connector plugins submitted
* Pull requests merged
* Issues resolved

---

# 15. MVP Scope

The first public release should include:

* User authentication
* Job search
* Saved searches
* Connector framework
* Initial ATS connectors
* Initial company connectors
* Telegram notifications
* Bookmarking
* Duplicate detection
* Dashboard
* Admin panel
* Docker deployment
* CI/CD pipeline
* Open-source documentation

Everything else should be treated as future enhancements.

---

# 16. Future Enhancements

* Browser push notifications
* Email digests
* Native mobile applications
* Semantic search using local AI models
* Salary estimation
* Skill extraction
* Hiring trend analysis
* Public REST API
* GraphQL API
* Plugin marketplace
* Team workspaces
* Organization dashboards

---

# 17. Guiding Principles

Every feature should prioritize:

* Speed
* Simplicity
* Transparency
* Extensibility
* Privacy
* Reliability
* Open-source collaboration

No feature should compromise user control over the application process or require paid third-party APIs as a prerequisite for core functionality.
