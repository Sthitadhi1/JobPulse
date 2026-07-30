# API_SPEC.md

# JobPulse API Specification

Version: 1.0

API Style: REST (v1)

Transport: HTTPS

Authentication: JWT Bearer Tokens

Data Format: JSON

---

# 1. API Principles

The API should be:

* RESTful
* Stateless
* Versioned
* Secure
* Well documented
* Predictable
* Backward compatible where practical

Every endpoint should return consistent response structures.

---

# 2. API Versioning

Base URL

```text
/api/v1
```

Future versions

```text
/api/v2
```

Breaking changes must only occur in new API versions.

---

# 3. Authentication

Authentication uses JWT.

Flow

User Login

↓

Access Token

↓

Refresh Token

↓

Authenticated Requests

Access tokens should be short-lived.

Refresh tokens should be revocable.

---

# 4. Standard Response Format

Successful responses

```json
{
  "success": true,
  "message": "Operation completed successfully.",
  "data": {},
  "meta": {}
}
```

Error responses

```json
{
  "success": false,
  "message": "Validation failed.",
  "errors": []
}
```

---

# 5. Authentication Endpoints

POST

/auth/register

Purpose

Create account.

---

POST

/auth/login

Returns

Access token

Refresh token

User profile

---

POST

/auth/logout

Invalidate session.

---

POST

/auth/refresh

Issue new access token.

---

GET

/auth/me

Return authenticated user.

---

PATCH

/auth/profile

Update profile.

---

PATCH

/auth/password

Change password.

---

DELETE

/auth/account

Delete account.

---

# 6. User Endpoints

GET

/users/me

Return user information.

---

PATCH

/users/preferences

Update

Theme

Timezone

Notifications

Language

Telegram settings

---

GET

/users/statistics

Return

Bookmarks

Applications

Saved searches

Notifications

Jobs matched

---

# 7. Search Endpoints

POST

/search

Run search.

Supports

Keywords

Boolean operators

Filters

Sorting

Pagination

---

GET

/search/history

Return previous searches.

---

DELETE

/search/history/{id}

Delete history entry.

---

POST

/search/saved

Create saved search.

---

GET

/search/saved

Return saved searches.

---

PATCH

/search/saved/{id}

Update search.

---

DELETE

/search/saved/{id}

Delete search.

---

PATCH

/search/saved/{id}/toggle

Enable

Disable monitoring

---

POST

/search/test

Run search without saving.

---

# 8. Job Endpoints

GET

/jobs

Return jobs.

Supports

Pagination

Filtering

Sorting

---

GET

/jobs/{id}

Return complete job details.

---

GET

/jobs/recent

Return newest jobs.

---

GET

/jobs/trending

Return trending companies.

---

GET

/jobs/company/{companyId}

Return company jobs.

---

GET

/jobs/source/{sourceId}

Return source jobs.

---

GET

/jobs/recommended

Future endpoint.

---

# 9. Bookmark Endpoints

POST

/bookmarks

Bookmark job.

---

GET

/bookmarks

Return bookmarks.

---

PATCH

/bookmarks/{id}

Move folder.

Update notes.

---

DELETE

/bookmarks/{id}

Remove bookmark.

---

# 10. Application Tracker

POST

/applications

Track application.

---

GET

/applications

Return tracked applications.

---

PATCH

/applications/{id}

Update status.

---

DELETE

/applications/{id}

Remove record.

---

# 11. Notification Endpoints

GET

/notifications

Return notifications.

---

PATCH

/notifications/{id}/read

Mark read.

---

DELETE

/notifications/{id}

Delete notification.

---

PATCH

/notifications/settings

Update preferences.

---

POST

/notifications/test

Send test notification.

---

# 12. Telegram Integration

POST

/telegram/connect

Generate secure connection flow.

---

POST

/telegram/disconnect

Remove Telegram association.

---

GET

/telegram/status

Return connection status.

---

POST

/telegram/test

Send test message.

---

# 13. Company Endpoints

GET

/companies

Return companies.

Supports

Filtering

Sorting

Pagination

---

GET

/companies/{id}

Return company.

---

GET

/companies/{id}/jobs

Company jobs.

---

GET

/companies/trending

Hiring trends.

---

# 14. Source Endpoints

GET

/sources

Return supported sources.

---

GET

/sources/{id}

Return source.

---

GET

/sources/health

Connector health.

---

# 15. Admin Endpoints

Protected.

Admin only.

GET

/admin/users

---

GET

/admin/jobs

---

GET

/admin/connectors

---

PATCH

/admin/connectors/{id}

Enable

Disable

Update interval

---

POST

/admin/connectors/{id}/run

Run connector manually.

---

GET

/admin/logs

---

GET

/admin/statistics

---

# 16. Connector API

Future contributor endpoints.

GET

/connectors

Return available connectors.

---

POST

/connectors/register

Community connector.

---

PATCH

/connectors/{id}

Update connector.

---

DELETE

/connectors/{id}

Remove connector.

---

# 17. Analytics Endpoints

GET

/analytics/dashboard

Return

Daily jobs

Weekly jobs

Companies

Locations

Sources

---

GET

/analytics/hiring

Hiring trends.

---

GET

/analytics/locations

Top locations.

---

GET

/analytics/companies

Top companies.

---

# 18. Pagination

Every list endpoint should support

page

limit

sort

order

Example

```text
/jobs?page=1&limit=25
```

Metadata

Current page

Total pages

Total records

Next page

Previous page

---

# 19. Filtering

Jobs

Location

Company

Remote

Salary

Experience

Employment Type

Source

Posted Within

Saved Searches

Active

Inactive

Notification Enabled

Companies

Industry

Type

Country

Hiring

---

# 20. Sorting

Newest

Oldest

Salary

Company

Relevance

Recently Updated

---

# 21. Rate Limiting

Unauthenticated

100 requests/hour

Authenticated

1000 requests/hour

Admin

Higher configurable limits

Connector endpoints should use separate internal rate controls.

---

# 22. Error Codes

400

Bad Request

401

Unauthorized

403

Forbidden

404

Not Found

409

Conflict

422

Validation Error

429

Too Many Requests

500

Internal Server Error

503

Service Unavailable

---

# 23. Validation

Every endpoint must validate

Input types

Length

Format

Required fields

Enum values

Dates

UUIDs

Malformed requests return structured validation errors.

---

# 24. Security

HTTPS only

JWT

CSRF protection where applicable

Input sanitization

Output encoding

Role-based authorization

Request size limits

Audit logging

Secure headers

---

# 25. API Documentation

Generate automatically using OpenAPI.

Expose

Swagger UI

OpenAPI JSON

Interactive documentation

Every endpoint must include

Description

Parameters

Request examples

Response examples

Error responses

Authentication requirements

---

# 26. WebSocket Support

Future endpoint

/ws

Events

new_job

job_updated

notification

connector_status

system_announcement

Heartbeat support should keep long-lived connections healthy.

---

# 27. Idempotency

Create operations should support idempotency where appropriate.

Repeated identical requests must not create duplicate resources.

---

# 28. Caching

Support HTTP caching headers for read-heavy endpoints.

Expose ETag and Last-Modified where beneficial.

---

# 29. API Performance Targets

Average GET response

<300 ms

Average POST response

<500 ms

Search endpoint

<500 ms

Authentication

<300 ms

Pagination queries

<300 ms

---

# 30. Design Principles

The API should be:

* Consistent
* Predictable
* Easy to consume
* Language agnostic
* Secure by default
* Extensible
* Well documented

Future mobile apps, browser extensions, desktop applications, and third-party integrations should all be able to use the same API without requiring separate backend implementations.
