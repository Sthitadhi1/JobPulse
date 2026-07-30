# MATCHING_ENGINE.md

# JobPulse Matching Engine

**Project:** JobPulse
**Version:** 1.0

---

# 1. Purpose

The Matching Engine continuously evaluates newly discovered jobs against every user's active saved searches and notification preferences.

Its responsibilities include:

* Matching jobs to user preferences
* Calculating match scores
* Eliminating duplicate notifications
* Prioritizing notifications
* Respecting user notification settings

The Matching Engine operates automatically whenever new jobs enter the system.

---

# 2. High-Level Flow

```text
New Job Discovered
        │
        ▼
Normalize Job
        │
        ▼
Load Active Saved Searches
        │
        ▼
Apply Mandatory Filters
        │
        ▼
Calculate Match Score
        │
        ▼
Check Duplicate Notifications
        │
        ▼
Queue Notification
        │
        ▼
Notification Engine
```

---

# 3. Matching Principles

The engine should:

* Favor precision over quantity.
* Avoid sending duplicate alerts.
* Notify users as quickly as practical.
* Produce deterministic results.
* Be explainable and configurable.

---

# 4. Matching Inputs

## Job Data

* Title
* Company
* Description
* Skills
* Location
* Remote type
* Employment type
* Experience
* Salary
* Posting date
* Source

---

## User Preferences

* Saved keywords
* Preferred locations
* Preferred companies
* Blocked companies
* Remote preference
* Employment type
* Experience range
* Salary expectations
* Notification channels
* Notification frequency

---

# 5. Mandatory Filters

Before scoring, remove jobs that fail required criteria.

Examples:

* Company is blocked.
* Experience exceeds user maximum.
* Employment type does not match.
* Remote preference incompatible.
* Search is disabled.

Jobs failing mandatory filters must not proceed to scoring.

---

# 6. Match Scoring

Each remaining job receives a weighted score.

Suggested signals:

| Signal                  | Example Weight |
| ----------------------- | -------------: |
| Exact title match       |             30 |
| Synonym title match     |             25 |
| Required skills overlap |             20 |
| Preferred location      |             10 |
| Remote preference       |             10 |
| Salary match            |             10 |
| Company preference      |             15 |
| Recency                 |             10 |

Weights should be configurable rather than hardcoded.

---

# 7. Skill Matching

Normalize skills before comparison.

Examples:

* JS → JavaScript
* TS → TypeScript
* Node → Node.js
* ML → Machine Learning

Support configurable aliases.

---

# 8. Title Matching

Examples:

User Search

```text
Software Engineer
```

Should also match:

* Software Developer
* SDE
* SDE I
* Graduate Engineer
* Application Engineer

Title mappings should be centrally managed.

---

# 9. Company Matching

Support:

Preferred Companies

Blocked Companies

Followed Companies

Users may receive notifications only from followed companies if they choose that mode.

---

# 10. Location Matching

Support multiple levels.

Examples:

Country

↓

State

↓

City

↓

Remote

Users may define multiple preferred locations.

---

# 11. Salary Matching

If salary data exists:

Compare:

* Minimum expectation
* Maximum expectation
* Currency

Missing salary data should not automatically reject a job unless explicitly configured by the user.

---

# 12. Freshness Bonus

Recent postings receive additional score.

Example policy:

* < 1 hour
* < 6 hours
* < 24 hours
* < 3 days
* Older

Exact scoring values should remain configurable.

---

# 13. Duplicate Prevention

Never notify the same user twice for the same job unless:

* The job has materially changed.
* The previous notification has expired according to platform policy.

Track notifications using stable job identifiers where available.

---

# 14. Notification Priority

Suggested levels:

Critical

High

Normal

Low

Priority influences queue ordering but not eligibility.

---

# 15. Batch Processing

The engine should process jobs in batches for efficiency while ensuring individual matching results remain isolated.

Batch size should be configurable.

---

# 16. Performance Goals

Target:

* Match a newly discovered job against active saved searches with low latency.
* Support horizontal scaling through worker processes.
* Avoid blocking connector ingestion.

Performance should be monitored continuously.

---

# 17. Explainability

For every notification, store why the match occurred.

Example:

* Exact title match
* Preferred location
* Matching skills
* Remote preference

This enables transparent UI explanations such as:

> "Matched because your saved search includes 'Python', 'Backend', and 'Remote'."

---

# 18. Failure Handling

If matching fails:

* Log the failure.
* Retry according to scheduler policy.
* Avoid sending partial or duplicate notifications.
* Continue processing unrelated jobs.

---

# 19. Future Enhancements

Possible future capabilities:

* AI-assisted relevance scoring
* Personalized ranking based on user interactions
* Learning from bookmarked and applied jobs
* Company affinity models
* Time-of-day notification optimization
* Multi-language matching

These features should remain optional and not replace deterministic matching without user control.

---

# 20. Success Criteria

The Matching Engine succeeds when it:

* Delivers relevant jobs to the correct users.
* Minimizes false positives.
* Avoids duplicate notifications.
* Explains why a job matched.
* Scales efficiently as users and job volume grow.

The engine should remain predictable, configurable, and easy to extend while serving as the decision layer between job discovery and notification delivery.
