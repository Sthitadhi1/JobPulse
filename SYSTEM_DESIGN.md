# SYSTEM_DESIGN.md

# JobPulse System Design

Version: 1.0

---

# 1. Architecture Philosophy

JobPulse should be designed as a modular, service-oriented application where every major responsibility is isolated into its own module.

The architecture should prioritize:

* Scalability
* Extensibility
* Fault tolerance
* Testability
* Observability
* Community contributions

Every component should be replaceable without affecting the rest of the platform.

---

# 2. High-Level Architecture

```text
                       Users
                          │
                Next.js Frontend
                          │
                     API Gateway
                          │
      ┌───────────────────┼───────────────────┐
      │                   │                   │
 Authentication      Job Service      Notification Service
      │                   │                   │
      │                   │                   │
      └─────────────── Database ──────────────┘
                          │
                    Scheduler Service
                          │
                  Source Connector Engine
                          │
         ┌────────────────┼────────────────┐
         │                │                │
     ATS Connectors   Company Pages   Public Sources
                          │
                    Normalization Layer
                          │
                  Duplicate Detection
                          │
                     PostgreSQL Storage
                          │
                  Notification Queue
                          │
                 Telegram / Email / Push
```

---

# 3. Core Services

The platform should be divided into the following logical services.

## Frontend Service

Responsibilities

* User authentication
* Dashboard
* Search
* Saved searches
* Bookmarks
* Analytics
* Notification settings
* Profile management

Technology

* Next.js
* React
* Tailwind CSS
* TypeScript

---

## API Service

Responsibilities

* REST API
* Authentication
* Validation
* Authorization
* Job queries
* User management
* Search management

Technology

* FastAPI

---

## Scheduler Service

Responsibilities

* Execute recurring connector jobs
* Queue connector execution
* Retry failed jobs
* Prioritize frequently changing sources

Scheduling intervals should be configurable.

Example

* Every minute
* Every five minutes
* Every fifteen minutes
* Hourly

---

## Source Connector Engine

The connector engine is responsible for collecting jobs from every supported source.

It should never know anything about users.

It should only return normalized job objects.

Every connector must implement the same interface.

---

## Normalization Service

Different sources expose different field names.

Example

Source A

Job Name

Source B

Title

Source C

Position

All become

title

Likewise

Office

City

Location

becomes

location

Every connector returns identical objects before saving.

---

## Duplicate Detection Service

Responsible for preventing duplicate jobs.

Possible matching fields

Company

Title

Location

Employment type

Posting date

Job ID

Canonical URL

Description similarity

The duplicate detection layer should be independent from connector logic.

---

## Notification Service

Responsible only for notifications.

Supported channels

Telegram

Email

Browser Push

Discord

Slack

Future channels should be plug-and-play.

---

## Search Service

Responsible for

Search indexing

Filtering

Sorting

Pagination

Saved search execution

Keyword parsing

---

## Analytics Service

Responsible for

Hiring statistics

Company trends

Location trends

Daily discovery metrics

Notification metrics

User analytics

---

## Admin Service

Responsible for

Connector status

Logs

Users

Monitoring

Configuration

Feature flags

---

# 4. Connector Architecture

Every supported source should be implemented as an independent connector.

Example

```text
connectors/

greenhouse/

lever/

ashby/

google/

amazon/

oracle/

adobe/

...
```

Every connector implements

```text
connect()

fetch()

parse()

normalize()

health_check()
```

No connector should directly access the database.

No connector should send notifications.

Its only responsibility is returning normalized jobs.

---

# 5. Connector Pipeline

```text
Scheduler

↓

Connector

↓

Raw HTML / JSON

↓

Parser

↓

Normalized Job

↓

Validation

↓

Duplicate Detection

↓

Database

↓

Notification Queue
```

Every stage should be independently testable.

---

# 6. Job Lifecycle

Job discovered

↓

Normalized

↓

Validated

↓

Duplicate checked

↓

Stored

↓

Matched against user searches

↓

Notifications generated

↓

Delivered

↓

Archived when expired

---

# 7. Search Engine

The search engine should support

Keyword search

Boolean operators

Location filtering

Experience filtering

Salary filtering

Company inclusion

Company exclusion

Sorting

Pagination

Search history

Saved searches

Initially use PostgreSQL Full-Text Search.

Design the abstraction so Elasticsearch or OpenSearch can replace it later without changing business logic.

---

# 8. Scheduler Design

The scheduler should support

Connector priority

Retry policies

Backoff strategies

Concurrent execution

Maximum execution time

Health monitoring

Each connector should declare

* Default interval
* Maximum runtime
* Retry count
* Timeout

---

# 9. Queue Architecture

Long-running work should never block API requests.

Use queues for

Connector execution

Notifications

Analytics

Statistics

Future AI tasks

The queue implementation should be replaceable.

---

# 10. Database Layer

The application should never execute raw SQL directly from business logic.

All database access should occur through a repository or ORM layer.

Responsibilities

Transactions

Validation

Caching

Connection pooling

Migration support

---

# 11. Caching Strategy

Cache

Frequently searched jobs

Company metadata

Search filters

Statistics

User settings

Connector metadata

Use Redis as the primary cache.

Fallback gracefully if Redis becomes unavailable.

---

# 12. Notification Pipeline

Job inserted

↓

Search matching

↓

Notification generated

↓

Queue

↓

Telegram

↓

Delivery confirmation

↓

Notification history

Failed deliveries should retry automatically.

---

# 13. Logging

Every service should produce structured logs.

Important events

Connector started

Connector completed

Connector failed

Notification sent

Notification failed

User login

Search created

Job discovered

Duplicate removed

Logs should support centralized aggregation in the future.

---

# 14. Monitoring

Monitor

CPU

Memory

Database

Queue

Connector latency

Notification latency

API latency

Search latency

Error rate

Success rate

Connector uptime

---

# 15. Security

JWT authentication

HTTPS

Password hashing

Role-based authorization

Input validation

Output encoding

Rate limiting

CORS

Secure cookies

Secrets management

Environment variables

---

# 16. Deployment Architecture

```text
Internet

↓

Reverse Proxy

↓

Frontend

↓

FastAPI

↓

PostgreSQL

↓

Redis

↓

Scheduler

↓

Connector Workers

↓

Notification Workers
```

Every service should be containerized.

Docker Compose should support local development.

The architecture should be compatible with Kubernetes in the future.

---

# 17. Scalability Strategy

The system should scale horizontally.

Frontend

Multiple instances

API

Multiple instances

Connector workers

Unlimited horizontal scaling

Notification workers

Independent scaling

Database

Read replicas

Connection pooling

Caching

Heavy read operations should prefer Redis.

---

# 18. Failure Recovery

If one connector fails

The remaining connectors continue.

If Redis fails

Application falls back to database.

If Telegram is unavailable

Notifications retry later.

If one source changes structure

Only that connector should require updating.

Failures must be isolated.

---

# 19. Engineering Standards

Every service must include

Unit tests

Integration tests

Health checks

Structured logging

Configuration through environment variables

Dependency injection where appropriate

Type annotations

Comprehensive documentation

No hardcoded credentials

No business logic inside controllers

No duplicated code across connectors

---

# 20. Future Expansion

The architecture should support adding

* Mobile applications
* GraphQL API
* Browser extension
* Desktop application
* AI-powered semantic search
* Organization dashboards
* Public developer API
* Plugin marketplace
* Multi-language interface

These additions should not require significant architectural changes due to the modular service boundaries defined above.
