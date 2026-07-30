# SCRAPER_ENGINE.md

# JobPulse Scraper Engine & Connector Framework

Version: 1.0

---

# 1. Purpose

The Scraper Engine is responsible for discovering publicly accessible job postings from supported job sources, normalizing them into a common schema, removing duplicates, validating data, and forwarding newly discovered jobs for storage and notification.

The Scraper Engine **must never**:

* Authenticate using a user's personal account.
* Fill application forms.
* Submit job applications.
* Circumvent authentication systems or CAPTCHAs.
* Attempt to bypass anti-bot protections.
* Store user credentials for third-party websites.

Its only responsibility is discovering publicly available job listings from supported sources.

---

# 2. Design Principles

The Scraper Engine should be:

* Plugin-based
* Modular
* Fault tolerant
* Independently testable
* Highly configurable
* Horizontally scalable
* Easy to extend
* Easy to monitor

Every connector should operate independently.

Failure in one connector must never affect any other connector.

---

# 3. Connector Categories

The engine should support multiple connector types.

### ATS Connectors

Examples:

* Greenhouse
* Lever
* Ashby
* Workday
* SmartRecruiters
* BambooHR
* Teamtailor
* Recruitee
* Jobvite
* iCIMS

---

### Company Career Page Connectors

Examples

* Google
* Microsoft
* Amazon
* Oracle
* Adobe
* NVIDIA
* Cisco
* Qualcomm
* Atlassian
* Zoho
* Salesforce

---

### Startup Connectors

Examples

* Wellfound
* YC Jobs

---

### Remote Job Connectors

Examples

Publicly accessible remote job providers that permit indexing.

---

### Community Connectors

Open-source contributors should be able to add additional connectors that comply with the project's contribution guidelines and applicable terms of use.

---

# 4. Folder Structure

```text
scrapers/

base/

    base_connector.py
    parser.py
    validator.py
    normalizer.py
    deduplicator.py

connectors/

    greenhouse/
    lever/
    ashby/
    workday/
    amazon/
    google/
    oracle/
    microsoft/
    adobe/
    ...

tests/

fixtures/

docs/
```

Each connector lives inside its own directory.

---

# 5. Base Connector Interface

Every connector must implement the same lifecycle.

Required methods

* initialize()
* fetch()
* parse()
* normalize()
* validate()
* health_check()
* shutdown()

The engine should never make assumptions about connector internals beyond this contract.

---

# 6. Connector Lifecycle

```text
Scheduler

↓

Initialize Connector

↓

Fetch Public Data

↓

Parse Response

↓

Normalize Fields

↓

Validate Schema

↓

Duplicate Detection

↓

Persist Jobs

↓

Queue Notifications

↓

Shutdown Connector
```

---

# 7. Connector Responsibilities

A connector is responsible only for:

* Retrieving publicly accessible job listings.
* Parsing raw responses.
* Returning normalized job objects.

A connector is **not** responsible for:

* Database access.
* Sending notifications.
* User matching.
* Authentication.
* Business logic.
* Analytics.

---

# 8. Normalized Job Schema

Every connector must return the same logical fields.

Required fields include:

* external_job_id
* company_name
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
* skills
* apply_url
* canonical_url
* posting_date
* discovered_at
* source_name
* source_type

Optional fields should be clearly documented.

---

# 9. Data Validation

Every normalized job should pass validation before storage.

Validation should check:

* Required fields.
* URL format.
* Date format.
* Salary ranges.
* Duplicate identifiers.
* Field lengths.
* Enum values.
* Character encoding.

Invalid jobs should be rejected and logged.

---

# 10. Duplicate Detection

The duplicate detection layer should be independent of connector implementations.

Matching signals may include:

* External job ID.
* Canonical URL.
* Company.
* Title.
* Location.
* Posting date.
* Normalized description hash.

Duplicates should update metadata where appropriate rather than creating new records.

---

# 11. Scheduler

The scheduler manages connector execution.

Connector configuration should include:

* Enabled/disabled state.
* Execution interval.
* Maximum runtime.
* Timeout.
* Retry count.
* Priority.
* Concurrency limits.

Execution intervals should be configurable.

---

# 12. Retry Strategy

Temporary failures should use exponential backoff.

Permanent failures should disable retries until the next scheduled execution.

Each connector should define:

* Maximum retries.
* Timeout.
* Cooldown period.

---

# 13. Health Monitoring

Every connector should expose health information.

Metrics include:

* Last successful execution.
* Average runtime.
* Success rate.
* Failure rate.
* Jobs discovered.
* Jobs added.
* Duplicate count.
* Validation failures.

The admin dashboard should display connector health.

---

# 14. Error Handling

Errors should be categorized.

Recoverable

* Temporary network issues.
* Timeouts.
* Rate limiting.

Non-recoverable

* Invalid configuration.
* Unsupported response format.
* Missing required parser.
* Schema violations.

Every error should be logged with sufficient context.

---

# 15. Logging

Connector logs should include:

* Connector name.
* Version.
* Start time.
* End time.
* Duration.
* Jobs fetched.
* Jobs added.
* Duplicates.
* Validation failures.
* Retry attempts.
* Exception details.

Logs should be structured and machine-readable.

---

# 16. Performance Requirements

Target performance:

* Connector initialization under 1 second.
* Parsing optimized for large result sets.
* Batch persistence where possible.
* Minimize unnecessary network requests.
* Reuse HTTP sessions where appropriate.

---

# 17. Source Configuration

Every connector should have its own configuration.

Typical configuration values:

* Source name.
* Base URL.
* Polling interval.
* Request timeout.
* Maximum pages.
* Maximum jobs per execution.
* Enable/disable flag.

Configuration should be externalized and not hardcoded.

---

# 18. Contribution Guidelines

Every new connector should include:

* Source documentation.
* Configuration example.
* Unit tests.
* Sample fixtures.
* Parsing tests.
* Health checks.
* Error handling.
* README.

A connector should not be merged without tests.

---

# 19. Testing Strategy

Each connector must include:

* Unit tests.
* Integration tests (where feasible).
* Parser validation tests.
* Normalization tests.
* Duplicate detection tests.
* Failure scenario tests.

Continuous integration should execute connector tests automatically.

---

# 20. Future Enhancements

The architecture should support:

* Incremental crawling.
* Change detection.
* Distributed workers.
* Connector auto-discovery.
* Plugin marketplace.
* Machine-learning-assisted field extraction.
* AI-powered semantic job classification (using optional local models).
* Distributed scheduling across multiple worker nodes.

The connector framework should remain backward compatible so community-maintained connectors continue to function as the platform evolves.
