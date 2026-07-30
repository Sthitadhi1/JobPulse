# DATABASE_DESIGN.md

# JobPulse Database Design

Version: 1.0

Database Engine: PostgreSQL

---

# 1. Database Philosophy

The database should be designed for:

* High read performance
* Fast filtering
* Fast search
* High write throughput
* Low duplication
* Easy migrations
* Strong data integrity
* Horizontal scalability
* Community extensibility

The schema should follow Third Normal Form (3NF) where practical while allowing selective denormalization for performance.

---

# 2. Core Entities

The platform revolves around these primary entities:

* Users
* Saved Searches
* Jobs
* Companies
* Job Sources
* Source Connectors
* Notifications
* Bookmarks
* Search History
* Job Applications (tracking only)
* User Preferences
* Connector Runs
* Connector Logs
* Roles
* Sessions
* Audit Logs

---

# 3. Entity Relationship Overview

```text
Users
 ├── Saved Searches
 ├── Notifications
 ├── Bookmarks
 ├── Search History
 ├── Sessions
 ├── Preferences
 └── Application Tracker

Jobs
 ├── Company
 ├── Source
 ├── Notifications
 ├── Bookmarks
 └── Applications

Companies
 └── Jobs

Sources
 └── Jobs

Connectors
 ├── Runs
 └── Logs
```

---

# 4. Users Table

Purpose

Stores registered users.

Fields

* id (UUID Primary Key)
* name
* email
* password_hash
* telegram_chat_id
* avatar_url
* role_id
* is_verified
* is_active
* last_login
* created_at
* updated_at

Indexes

* email UNIQUE
* telegram_chat_id
* created_at

---

# 5. Roles Table

Fields

* id
* role_name

Example

Admin

Moderator

User

Contributor

---

# 6. User Preferences

Stores user settings.

Fields

* id
* user_id
* theme
* timezone
* language
* notification_enabled
* telegram_enabled
* email_enabled
* preferred_locations
* preferred_job_types
* created_at

---

# 7. Saved Searches

Purpose

Stores continuous searches.

Fields

* id
* user_id
* search_name
* query
* locations
* experience_levels
* salary_min
* salary_max
* employment_types
* include_companies
* exclude_companies
* keywords
* is_active
* created_at
* updated_at

Indexes

user_id

query

is_active

---

# 8. Jobs Table

Purpose

Stores normalized jobs.

Fields

* id (UUID)
* company_id
* source_id
* external_job_id
* title
* description
* location
* remote_type
* employment_type
* experience_min
* experience_max
* salary_min
* salary_max
* currency
* apply_url
* canonical_url
* posting_date
* discovered_at
* expires_at
* hash_signature
* status

Indexes

title

company_id

location

posting_date DESC

discovered_at DESC

GIN Full Text Index

status

---

# 9. Companies Table

Fields

* id
* company_name
* website
* careers_url
* logo_url
* company_type
* industry
* country
* city
* is_active
* created_at

Example Types

Product

Service

Startup

Government

Remote

---

# 10. Job Sources

Purpose

Stores every source.

Examples

Greenhouse

Lever

Ashby

Workday

Company Career Page

Remote Board

Fields

* id
* source_name
* source_type
* website
* is_enabled
* created_at

---

# 11. Source Connectors

Stores connector metadata.

Fields

* id
* connector_name
* version
* maintainer
* supported_source
* execution_interval
* timeout_seconds
* retry_limit
* health_status
* last_run
* created_at

---

# 12. Connector Runs

Every execution creates one record.

Fields

* id
* connector_id
* started_at
* completed_at
* jobs_found
* jobs_added
* duplicates
* failures
* duration_ms
* status

---

# 13. Connector Logs

Fields

* id
* connector_run_id
* level
* message
* timestamp

---

# 14. Notifications

Fields

* id
* user_id
* job_id
* channel
* delivery_status
* sent_at
* delivered_at
* retry_count

Channels

Telegram

Email

Browser Push

Discord

Slack

---

# 15. Bookmarks

Fields

* id
* user_id
* job_id
* folder
* notes
* created_at

Folders

Interested

Applied

Interview

Offer

Rejected

Archive

---

# 16. Search History

Stores manual searches.

Fields

* id
* user_id
* query
* filters
* searched_at

---

# 17. Application Tracker

This does NOT submit applications.

Only stores user progress.

Fields

* id
* user_id
* job_id
* status
* notes
* updated_at

Statuses

Interested

Applied

OA

Interview

Offer

Rejected

Accepted

---

# 18. Sessions

Fields

* id
* user_id
* refresh_token_hash
* device
* ip_address
* expires_at
* created_at

---

# 19. Audit Logs

Fields

* id
* user_id
* action
* entity
* entity_id
* timestamp
* metadata

---

# 20. Duplicate Detection Strategy

Every job should generate a deterministic hash.

Recommended inputs

Company

Title

Location

Posting Date

Canonical URL

Normalized Description

Hash should be indexed.

Duplicates should never create new job rows.

Instead, update discovery metadata if required.

---

# 21. Search Optimization

Use PostgreSQL Full-Text Search.

Create GIN indexes for

Title

Description

Skills (future)

Location

Company

Support ranking based on

Recency

Keyword relevance

Company filters

Location filters

---

# 22. Index Strategy

High-priority indexes

Jobs(posting_date DESC)

Jobs(discovered_at DESC)

Jobs(company_id)

Jobs(location)

Jobs(status)

SavedSearches(user_id)

Notifications(user_id)

Bookmarks(user_id)

ConnectorRuns(connector_id)

Companies(company_name)

Unique indexes

Users(email)

Jobs(hash_signature)

---

# 23. Constraints

Every foreign key should enforce referential integrity.

Cascade deletes only where appropriate.

Jobs should never be deleted when a user deletes their account.

Bookmarks and notifications should cascade with user deletion.

---

# 24. Data Retention

Jobs

Archive expired jobs after configurable retention period.

Connector logs

Retain for 90 days by default.

Audit logs

Retain indefinitely unless configured otherwise.

Notifications

Retain delivery history.

---

# 25. Performance Targets

Search queries

< 300 ms

Dashboard

< 500 ms

Bookmark operations

< 100 ms

Notification lookup

< 100 ms

Connector inserts

Batch optimized

---

# 26. Migration Strategy

Use versioned migrations.

Every schema change must

* be reversible
* preserve existing data
* include migration tests

Never modify production tables manually.

---

# 27. ORM Standards

The ORM layer should:

* Use UUID primary keys.
* Support optimistic locking where appropriate.
* Validate entities before persistence.
* Avoid N+1 queries.
* Use eager loading only when justified.
* Encapsulate database access in repositories.

---

# 28. Future Tables

Reserve schema flexibility for:

* Saved Filters
* Browser Push Devices
* AI Search Cache
* Resume Match Scores (optional)
* Company Hiring Trends
* Skill Taxonomy
* Salary Benchmarks
* Public API Keys
* Plugin Marketplace Metadata

---

# 29. Backup and Recovery

Support:

* Daily automated backups.
* Point-in-time recovery (where infrastructure permits).
* Backup verification.
* Disaster recovery documentation.

Database restoration should preserve UUID integrity and foreign key relationships.

---

# 30. Design Principles

The database must prioritize:

* Data integrity
* Fast search
* Efficient indexing
* Horizontal scalability
* Maintainability
* Extensibility
* Auditability
* Minimal duplication

Every new feature should integrate with the existing schema through well-defined relationships rather than introducing redundant data structures.
