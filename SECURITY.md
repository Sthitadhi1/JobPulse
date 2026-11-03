# Security Policy

## Reporting a vulnerability

Please **do not open a public issue** for security problems.

Report them privately through GitHub's
[private vulnerability reporting](https://github.com/Sthitadhi1/JobPulse/security/advisories/new)
form. Include:

- the affected endpoint, file, or feature
- steps to reproduce (a request/response pair is ideal)
- the impact you believe it has

You should get an acknowledgement within 7 days. Once a fix ships, we'll credit you in
the release notes unless you'd rather stay anonymous.

## Supported versions

Only the latest commit on `master` (and the live demo built from it) receives security fixes.

## Operator checklist

If you self-host JobPulse, before exposing it to the internet:

- Set `ADMIN_EMAILS` to the accounts allowed to post/unlist jobs and trigger crawls.
- Set `SCHEDULER_SECRET` to a long random value if you call `/api/v1/admin/connectors/*` from cron.
- Configure SMTP so users can receive password-reset codes.
- Set `SECURE_COOKIES=true` when serving over HTTPS, and restrict `ALLOWED_ORIGINS`.
