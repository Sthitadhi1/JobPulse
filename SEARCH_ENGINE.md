# SEARCH_ENGINE.md

# JobPulse Search Engine Design

**Project:** JobPulse
**Version:** 1.0

---

# 1. Purpose

The Search Engine is responsible for helping users quickly discover relevant job opportunities from the jobs collected by the connector framework.

It provides:

* Fast keyword search
* Advanced filtering
* Boolean search
* Sorting
* Autocomplete
* Synonym matching
* Saved searches
* Search history
* Ranking

The Search Engine **does not** scrape jobs directly. It operates only on normalized job data already stored in the database.

---

# 2. Goals

The Search Engine should:

* Return relevant results in under 500 ms for common queries.
* Support flexible search expressions.
* Handle millions of job records through scalable indexing strategies.
* Produce consistent results across different job sources.
* Be extensible for future AI-assisted ranking.

---

# 3. High-Level Architecture

```text
User Query
      │
      ▼
Query Parser
      │
      ▼
Normalizer
      │
      ▼
Filter Engine
      │
      ▼
Search Index
      │
      ▼
Ranking Engine
      │
      ▼
Pagination
      │
      ▼
Search Results
```

---

# 4. Searchable Fields

Users should be able to search by:

* Job title
* Company
* Skills
* Location
* Employment type
* Remote type
* Experience range
* Salary (when available)
* Source
* Posting date
* Description
* Keywords

---

# 5. Search Types

## Simple Search

Example

```
Software Engineer
```

---

## Phrase Search

Example

```
"Machine Learning Engineer"
```

Matches exact phrases.

---

## Boolean Search

Supported operators:

```
AND
OR
NOT
```

Example

```
Backend AND Python
```

---

Example

```
Java OR Kotlin
```

---

Example

```
React NOT Senior
```

---

## Multi-Keyword Search

Example

```
Python FastAPI PostgreSQL
```

Should prioritize jobs matching all terms while still returning partial matches.

---

# 6. Supported Filters

Users should be able to filter by:

### Experience

* Fresher
* 0–1
* 1–3
* 3–5
* 5+

---

### Employment Type

* Full-time
* Internship
* Contract
* Part-time
* Temporary

---

### Work Mode

* Remote
* Hybrid
* On-site

---

### Location

Country

State

City

---

### Salary

Minimum salary

Maximum salary

Currency

---

### Company

Include companies

Exclude companies

---

### Source

Filter by connector/source.

---

### Posted Within

* 24 hours
* 3 days
* 7 days
* 14 days
* 30 days

---

# 7. Query Normalization

Normalize user input before searching.

Examples

```
software engineer
```

↓

```
Software Engineer
```

---

Trim whitespace.

Normalize case.

Remove duplicate spaces.

Normalize punctuation.

---

# 8. Synonym Dictionary

Equivalent titles should improve recall.

Examples

```
Software Engineer

↓

SDE

↓

Software Developer

↓

Application Developer
```

---

Another example

```
Machine Learning Engineer

↓

ML Engineer

↓

AI Engineer
```

The synonym dictionary should be configurable and version-controlled.

---

# 9. Ranking Strategy

Results should be ranked using multiple weighted signals.

Suggested signals:

* Exact title match
* Phrase match
* Keyword frequency
* Skills overlap
* Company match
* Location match
* Posting recency
* Remote preference
* Salary availability

The weighting should be configurable rather than hardcoded.

---

# 10. Sorting

Users may sort by:

* Relevance (default)
* Newest
* Oldest
* Salary (ascending)
* Salary (descending)
* Company (A–Z)

---

# 11. Pagination

Support:

* Configurable page size
* Cursor-based pagination (preferred for large datasets)
* Traditional page numbers for simple navigation if required by the UI

The API should return pagination metadata such as total results, next cursor, and page size.

---

# 12. Autocomplete

Autocomplete should suggest:

* Job titles
* Companies
* Skills
* Locations

Suggestions should be based on indexed data and ordered by relevance or popularity.

---

# 13. Saved Searches

A saved search stores:

* Keywords
* Filters
* Sorting preference
* Notification preference

Users should be able to:

* Create
* Edit
* Duplicate
* Delete
* Enable/Disable

---

# 14. Search History

Store recent searches for signed-in users.

Each record should include:

* Query
* Filters
* Timestamp

Users can:

* Re-run
* Save
* Delete

---

# 15. Performance Targets

Target search latency:

* < 500 ms for common searches
* < 1 second for complex filtered searches

Indexes should be reviewed regularly as the dataset grows.

---

# 16. Caching

Cache frequently requested:

* Popular searches
* Autocomplete suggestions
* Company lists

Cache invalidation should occur when relevant indexed data changes.

---

# 17. Indexing Strategy

Indexes should prioritize commonly searched fields such as:

* Job title
* Company
* Location
* Posting date
* Employment type

The indexing approach should evolve as the dataset and search requirements grow.

---

# 18. Security

The search service should:

* Validate all inputs
* Prevent injection attacks
* Enforce API rate limits
* Respect authentication and authorization rules for user-specific data

---

# 19. Future Enhancements

Potential future improvements include:

* Semantic search using vector embeddings
* Personalized ranking based on user preferences
* Natural language search (e.g., "remote Python jobs in Bengaluru")
* Typo tolerance
* Related search suggestions
* Trending searches

These enhancements should be optional and designed to avoid disrupting the core search experience.

---

# 20. Success Criteria

The Search Engine should enable users to:

* Find relevant jobs quickly.
* Refine results with intuitive filters.
* Save searches for continuous monitoring.
* Receive consistent, predictable results across all supported job sources.

The design should remain scalable, maintainable, and extensible as JobPulse grows in both users and supported connectors.
