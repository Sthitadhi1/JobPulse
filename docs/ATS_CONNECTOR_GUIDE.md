# JobPulse v2 — ATS Connector Guide

## Adding a New ATS Connector

To add support for a new Applicant Tracking System (ATS):

1. **Create Connector Class**: Subclass `BaseConnector` in `backend/app/connectors/ats/`.
2. **Implement Stage 1 (`stage1_discover`)**: Visit company board API/URL, extract individual candidate URLs, return un-normalized item dicts.
3. **Implement Stage 2 (`stage2_extract`)**: Fetch candidate job page, extract `title`, `description`, `department`, `location`, `remote_type`, `employment_type`, `experience_level`, and `external_apply_url`. Store `None` for unavailable fields.
4. **Register in `two_stage_crawler.py`**: Add mapping in `self.ats_map`.
5. **Add Unit Tests**: Include test cases in `tests/test_engine.py`.
