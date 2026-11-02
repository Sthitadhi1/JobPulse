# JobPulse v2 — Scheduler & Failure Isolation

## Architectural Principles

1. **Independent Execution**: Every ATS connector runs in its own isolated async context.
2. **Failure Isolation**: One failing or rate-limited connector will never stop or block other connectors (`return_exceptions=True`).
3. **Execution Logging**: Detailed records logged in `connector_executions` table (`duration_ms`, `jobs_discovered`, `errors_count`).
4. **Health Diagnostics**: Dynamic health score calculated from execution history in `connector_health` table.

```mermaid
graph TD
    A[Scheduler Trigger] --> B[Load Connector Registry]
    B --> C[Connector 1: Greenhouse]
    B --> D[Connector 2: Lever]
    B --> E[Connector 3: Workday]
    B --> F[Connector 4: Custom HTML]
    C -->|Success| G[Deduplicate & Persist]
    D -->|Success| G
    E -->|HTTP 429 Rate Limit| H[Log Error & Continue]
    F -->|Success| G
    H --> I[Update ConnectorHealth status=DEGRADED]
    G --> J[Run Verification Batch]
    J --> K[Dispatch Telegram Alerts]
```
