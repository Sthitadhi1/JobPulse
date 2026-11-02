# Contributing to JobPulse

Thanks for helping make job discovery free and open for everyone. Contributions of any size are
welcome: a new company in the registry, a connector for another ATS, a bug fix, or a docs tweak.

By participating you agree to follow the [Code of Conduct](../CODE_OF_CONDUCT.md).

## Good first contributions

- **Add a company.** Append an entry to
  [`backend/app/connectors/config/companies.json`](../backend/app/connectors/config/companies.json).
  See the [Company Registry Guide](../docs/COMPANY_REGISTRY_GUIDE.md) for the schema. Prefer
  companies whose careers page runs on a supported ATS (Greenhouse, Lever, Ashby, SmartRecruiters,
  Workday, …) so jobs come from an official public endpoint.
- **Add an ATS connector.** Follow the [ATS Connector Guide](../docs/ATS_CONNECTOR_GUIDE.md).
- **Fix a bug or improve the UI.** Look for issues labelled `good first issue` or `help wanted`.

## Development setup

Requires Python 3.11+.

```bash
git clone https://github.com/<your-username>/JobPulse.git
cd JobPulse
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env             # optional; defaults work for local dev
python run_dev.py
```

Open http://localhost:8000/dashboard/. API docs live at http://localhost:8000/docs.

To try admin-only features locally (posting jobs), sign up and add your email to `ADMIN_EMAILS`
in `.env`. Without SMTP configured, password-reset codes are printed to the server console.

## Running tests

```bash
python -m unittest discover -s tests -v
```

The same suite runs in GitHub Actions on every pull request. Some connector tests make real
network requests, so a full run takes a minute or two.

## Pull requests

1. Fork the repo and create a branch from `master` (`feat/greenhouse-pagination`, `fix/kanban-drag`).
2. Keep each PR focused on one change, and add or update tests for behaviour you change.
3. Use [Conventional Commit](https://www.conventionalcommits.org/) prefixes in commit messages
   (`feat:`, `fix:`, `docs:`, `test:`, `refactor:`, `ci:`).
4. Make sure the test suite passes, then open the PR and fill in the template.

## Ground rules for data sources

JobPulse should only index jobs from **public, official sources**: employer career pages and the
public job-board APIs that ATS vendors provide for that purpose. Please don't submit connectors
that log in to sites, bypass rate limits or bot protection, or collect personal data about
candidates or recruiters.

## Reporting security issues

Please don't file public issues for vulnerabilities; see [SECURITY.md](../SECURITY.md).
