# CONTRIBUTING.md

# Contributing to JobPulse

First of all, thank you for your interest in contributing to **JobPulse**! 🎉

Our goal is to build a fast, reliable, open-source platform that helps students and professionals discover new job opportunities from publicly accessible sources.

Whether you're fixing a typo, improving documentation, building a connector, or implementing a new feature, your contributions are welcome.

---

# Table of Contents

1. Code of Conduct
2. Ways to Contribute
3. Development Setup
4. Repository Structure
5. Branching Strategy
6. Coding Standards
7. Testing Guidelines
8. Pull Request Process
9. Issue Guidelines
10. Connector Development Guide
11. Documentation Standards
12. Release Process
13. Security Policy
14. Community & Governance

---

# 1. Code of Conduct

We strive to create a respectful and inclusive community.

Contributors are expected to:

* Be respectful.
* Be constructive.
* Welcome new contributors.
* Focus on technical discussions.
* Provide helpful code reviews.
* Assume good intent.

Harassment, discrimination, or abusive behavior will not be tolerated.

---

# 2. Ways to Contribute

You can contribute by:

* Fixing bugs
* Improving documentation
* Creating new connectors
* Writing tests
* Improving UI/UX
* Optimizing performance
* Reporting issues
* Reviewing pull requests
* Translating documentation (future)
* Suggesting new features

Not every contribution needs to involve writing code.

---

# 3. Development Setup

## Requirements

* Git
* Docker
* Docker Compose
* Node.js (LTS)
* Python 3.12+
* PostgreSQL
* Redis (if enabled)

## Installation

1. Fork the repository.
2. Clone your fork.
3. Create a feature branch.
4. Install frontend and backend dependencies.
5. Copy the example environment configuration.
6. Start the development environment.
7. Run tests before making changes.

The project should provide scripts so contributors can start with minimal manual configuration.

---

# 4. Repository Structure

```text
backend/
frontend/
connectors/
shared/
docs/
tests/
scripts/
docker/
.github/
```

Documentation should be stored under `docs/`.

Each connector should have its own directory.

---

# 5. Branching Strategy

### Main

Production-ready code only.

### Develop

Integration branch for upcoming releases.

### Feature Branches

Naming convention:

```
feature/job-search
feature/greenhouse-connector
feature/telegram-notifications
```

### Bug Fixes

```
fix/search-pagination
fix/login-validation
```

### Documentation

```
docs/api-spec
docs/contributing
```

---

# 6. Commit Message Convention

Use descriptive commit messages.

Examples:

```
feat: add greenhouse connector

fix: resolve duplicate detection bug

docs: update deployment guide

refactor: simplify scheduler service

test: add integration tests for search API

chore: update dependencies
```

Avoid vague messages such as:

* update
* changes
* fixes
* work
* misc

---

# 7. Coding Standards

## General

* Keep functions focused on one responsibility.
* Prefer readability over cleverness.
* Avoid unnecessary complexity.
* Remove unused code before submitting.

## Backend

* Follow consistent formatting.
* Use type hints where applicable.
* Validate external input.
* Handle errors explicitly.

## Frontend

* Use reusable components.
* Avoid duplicated UI logic.
* Keep components small and composable.
* Ensure responsive layouts.

---

# 8. Testing Requirements

Every contribution should include tests where practical.

Expected test types:

* Unit tests
* Integration tests
* API tests
* UI component tests
* Connector parsing tests

A pull request should not reduce overall test quality.

---

# 9. Pull Request Checklist

Before opening a PR, ensure:

* Code builds successfully.
* Tests pass.
* Documentation is updated if needed.
* Linting passes.
* No debug code remains.
* New configuration is documented.
* Screenshots are included for UI changes.
* Breaking changes are clearly described.

---

# 10. Code Review Guidelines

Reviewers should check:

* Correctness
* Readability
* Performance
* Security
* Maintainability
* Test coverage
* Documentation updates

Feedback should be constructive and specific.

---

# 11. Issue Guidelines

Before opening an issue:

* Search existing issues.
* Reproduce the problem.
* Include logs where relevant.
* Describe expected behavior.
* Describe actual behavior.
* Provide reproduction steps.

For feature requests:

* Explain the problem.
* Describe the proposed solution.
* Mention possible alternatives.
* Explain the user benefit.

---

# 12. Connector Development Guide

Connectors must:

* Follow the base connector interface.
* Retrieve only publicly accessible job listings.
* Normalize all fields to the common schema.
* Handle errors gracefully.
* Include automated tests.
* Include documentation.
* Pass validation before merging.

Every connector should contain:

```
README.md
config.example
tests/
fixtures/
connector implementation
```

---

# 13. Documentation Standards

Documentation should be:

* Accurate
* Versioned
* Easy to follow
* Updated alongside code changes

Whenever a feature changes, update the relevant documentation in the same pull request.

---

# 14. Security Policy

If you discover a security issue:

* Do not disclose it publicly.
* Contact the maintainers through the project's private security contact.
* Provide reproduction steps.
* Allow time for investigation and remediation before public discussion.

Security-related pull requests should be reviewed with priority.

---

# 15. Release Process

Releases should follow Semantic Versioning:

* MAJOR: incompatible API or architecture changes
* MINOR: backward-compatible features
* PATCH: bug fixes and small improvements

Each release should include:

* Changelog
* Migration notes (if required)
* Updated documentation
* Version tag
* Release announcement

---

# 16. Community Governance

Maintainers are responsible for:

* Reviewing pull requests
* Managing releases
* Maintaining documentation
* Resolving disputes
* Setting project direction

Contributors are encouraged to:

* Participate in discussions
* Review code
* Improve documentation
* Mentor newcomers
* Suggest improvements

Project decisions should be transparent and documented whenever possible.

---

# 17. Recognition

We value every contribution.

Contributors may be recognized through:

* GitHub Contributors page
* Release notes
* Project acknowledgements
* Community showcases

Recognition is based on meaningful contributions, not just the number of commits.

---

# 18. Roadmap Participation

Community members are encouraged to:

* Vote on feature proposals
* Suggest new connectors
* Help prioritize issues
* Participate in beta testing
* Review roadmap updates

The roadmap will evolve based on community feedback and project goals.

---

# 19. Final Notes

JobPulse aims to be a long-term community-driven project focused on helping people discover job opportunities quickly and reliably.

We welcome contributors of all experience levels. If you're unsure where to start, look for issues labeled **good first issue** or **help wanted**, or contribute by improving documentation and tests.

Thank you for helping make JobPulse better for everyone.
