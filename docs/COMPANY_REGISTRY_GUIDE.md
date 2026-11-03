# JobPulse v2 — Company Registry Guide

## Overview

The Company Registry is the single source of truth for company definitions in JobPulse.
All company listings originate from entries in `company_registry.json` or the database `company_registry` table.

## Entry Schema

```json
{
  "id": "vercel",
  "name": "Vercel",
  "category": "Product Company",
  "careers_url": "https://vercel.com/careers",
  "ats_provider": "greenhouse",
  "board_token": "vercel",
  "country": "India",
  "priority": 5,
  "crawl_interval": 60,
  "enabled": true,
  "supported_locations": ["Remote", "Bengaluru"],
  "tags": ["Frontend", "Cloud", "Next.js"]
}
```

---

## Supported `ats_provider` Values

- `greenhouse`
- `lever`
- `workday`
- `ashby`
- `smartrecruiters`
- `teamtailor`
- `successfactors`
- `oracle_taleo`
- `recruitee`
- `jobvite`
- `custom` (Generic HTML)
