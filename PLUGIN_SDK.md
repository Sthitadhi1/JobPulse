# PLUGIN_SDK.md

# JobPulse Plugin SDK

**Project:** JobPulse
**Version:** 1.0

---

# 1. Purpose

The Plugin SDK defines how contributors create, test, and maintain **connectors** that integrate new job sources into JobPulse.

A connector is responsible for retrieving publicly accessible job listings from a supported source and transforming them into JobPulse's normalized job schema.

The SDK exists to ensure:

* Consistency
* Reliability
* Maintainability
* Testability
* Backward compatibility

---

# 2. Design Goals

Every connector should be:

* Independent
* Stateless
* Easy to test
* Configurable
* Fault tolerant
* Versioned
* Replaceable

A connector must never require changes to the JobPulse core application.

---

# 3. Connector Lifecycle

```text
Initialize
      │
      ▼
Load Configuration
      │
      ▼
Health Check
      │
      ▼
Fetch Public Jobs
      │
      ▼
Parse Data
      │
      ▼
Normalize Fields
      │
      ▼
Validate Schema
      │
      ▼
Return Job Collection
      │
      ▼
Shutdown
```

---

# 4. Connector Responsibilities

A connector **must**:

* Retrieve publicly accessible job listings
* Parse responses
* Normalize fields
* Validate required data
* Return normalized jobs
* Handle transient failures
* Report health status

A connector **must not**:

* Write directly to the database
* Send notifications
* Match users
* Authenticate with user accounts
* Submit job applications
* Bypass authentication systems or CAPTCHAs

---

# 5. Connector Folder Structure

```text
connectors/
└── example_connector/
    ├── README.md
    ├── connector.py
    ├── parser.py
    ├── normalizer.py
    ├── validator.py
    ├── config.example.yaml
    ├── tests/
    └── fixtures/
```

Every connector should be self-contained.

---

# 6. Required Metadata

Each connector should expose metadata including:

* Connector name
* Version
* Maintainer
* Source name
* Source website
* Connector type
* Supported regions
* License compatibility

This metadata is used by the admin dashboard and diagnostics.

---

# 7. Configuration

Configuration should be externalized.

Typical settings include:

* Base URL
* Request timeout
* Polling interval
* Maximum pages
* Maximum jobs per run
* User agent (if required)
* Retry limits

Configuration values should not be hardcoded.

---

# 8. Normalized Job Schema

Every connector must return jobs using the shared schema.

Required fields include:

* External Job ID
* Job Title
* Company Name
* Description
* Location
* Employment Type
* Remote Type
* Experience
* Apply URL
* Canonical URL
* Source
* Posting Date
* Discovery Timestamp

Optional fields may include:

* Salary
* Skills
* Benefits
* Department

---

# 9. Validation

Before returning jobs, connectors should verify:

* Required fields exist
* URLs are valid
* Dates are parseable
* Text fields are within supported limits
* Enumerated values match expected options

Invalid records should be skipped and logged.

---

# 10. Error Handling

Recoverable errors:

* Temporary network failures
* HTTP timeouts
* Rate limiting
* Transient parsing issues

Non-recoverable errors:

* Invalid configuration
* Unsupported response format
* Missing required fields

Recoverable failures should trigger retries according to scheduler policy.

---

# 11. Logging

Every connector should produce structured logs.

Recommended log fields:

* Connector name
* Version
* Start time
* End time
* Jobs fetched
* Jobs returned
* Errors
* Retry count
* Duration

Logs should be suitable for automated monitoring.

---

# 12. Health Checks

Connectors should report:

* Healthy
* Degraded
* Unavailable

Health reports should include:

* Last successful execution
* Average runtime
* Failure count
* Recent error summary

---

# 13. Testing Requirements

Every connector should include:

* Unit tests
* Parser tests
* Normalization tests
* Validation tests
* Error handling tests

Where practical, include fixtures representing expected source responses.

---

# 14. Versioning

Connector versions should follow Semantic Versioning.

* MAJOR: Breaking changes
* MINOR: New functionality
* PATCH: Bug fixes

Version history should be documented in the connector's README.

---

# 15. Compatibility

Connectors should declare the minimum supported JobPulse SDK version.

Core changes that affect connector interfaces should provide migration guidance.

---

# 16. Security

Connectors should:

* Avoid logging sensitive information
* Validate external input
* Use secure network communication
* Respect robots.txt and publicly available access policies where applicable
* Avoid aggressive request rates

---

# 17. Performance

Target goals:

* Fast initialization
* Efficient parsing
* Minimal network requests
* Low memory usage
* Predictable execution time

Connector performance should be measurable through monitoring metrics.

---

# 18. Documentation

Each connector must provide a README describing:

* Purpose
* Supported source
* Configuration
* Limitations
* Testing instructions
* Maintenance notes

Good documentation is a requirement for acceptance into the main repository.

---

# 19. Contribution Checklist

Before submitting a connector:

* Implementation completed
* Tests pass
* Documentation updated
* Configuration example included
* Logging implemented
* Validation implemented
* Health checks implemented
* Code reviewed locally

Maintainers may request revisions before merging.

---

# 20. Future SDK Enhancements

Potential future capabilities include:

* Connector generator CLI
* Shared parsing utilities
* Automatic schema validation
* Connector marketplace
* Plugin signing
* Dependency isolation
* Runtime sandboxing

These enhancements should remain compatible with existing connectors whenever possible.

---

# Success Criteria

A contributor should be able to:

1. Read this SDK.
2. Build a new connector.
3. Test it locally.
4. Submit it for review.
5. Have it integrated into JobPulse without modifying the core platform.

The SDK should encourage a healthy ecosystem of community-maintained connectors while preserving consistency, quality, and maintainability across the project.
