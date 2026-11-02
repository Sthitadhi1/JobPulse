# JobPulse v2 — Database ER Diagram & Indexes

## ER Diagram

```mermaid
erDiagram
    CompanyRegistry ||--o{ Job : "defines source"
    Job ||--o{ Bookmark : "saved by"
    Job ||--o{ ApplicationTracker : "tracked by"
    Job ||--o{ NotificationLog : "triggers"
    SavedSearch ||--o{ NotificationLog : "generates"

    Job {
        int id PK
        string external_job_id IX
        string title IX
        string company IX
        string department IX
        string location IX
        string experience_level IX
        string job_url IX
        string external_apply_url
        string source IX
        string status IX
        string verification_status IX
        datetime first_seen IX
        datetime last_seen IX
        datetime last_verified IX
        datetime posted_at IX
        string hash_signature UK
    }

    ConnectorHealth {
        int id PK
        string name UK
        string status
        float average_runtime_ms
        int total_jobs_indexed
    }

    ConnectorExecution {
        int id PK
        string connector_name IX
        float duration_ms
        int jobs_discovered
        int errors_count
        string status IX
    }
```

---

## Indexing Strategy (Step 18)

- `idx_jobs_company_exp_status`: Compound index on `(company, experience_level, status)` for fast search queries.
- `idx_jobs_verification_status`: Compound index on `(verification_status, status)` for background verification workers.
- Individual indexes on `external_job_id`, `company`, `location`, `experience_level`, `job_url`, `source`, `verification_status`, `posted_at`.
