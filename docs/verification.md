# Verified presentation state — 12 October 2026

The Docker deployment supersedes the earlier SQLite preview verification.

| Executed check | Evidence |
|---|---|
| GitHub version control | main/develop, merged PRs 1 and 2; exercise/git-conflict-resolved contains a real resolved conflict; tag v1.0.0-demo |
| Docker and Compose | Jenkins built application images and deployed separate production/staging frontend, backend and PostgreSQL services |
| Jenkins CI | 32 backend tests passed; main build 4 and develop build 5 SUCCESS |
| CD | GitHub polling retained by user choice; main deploys production, develop deploys staging; feature branch builds only |
| Persistence | develop build 5 inserted a marker, restarted PostgreSQL, verified persistence and cleaned the marker |
| Rollback | develop build 5 deployed a deliberately broken frontend; smoke failed and both previous image IDs were restored; authenticated smoke then passed |
| Monitoring | Prometheus backend, cAdvisor and Prometheus targets UP; Grafana dashboard provisioned |
| Alert recovery | Controlled staging outage triggered BackendDown; backend restored, alert cleared and final authenticated smoke passed |
| Jira | HDEV project, epic HDEV-3, nine stories and active HDEV Sprint 1; eight verified stories Done, presentation review In Progress |
| Presenter login | presenter@helpdesk.local verified as admin on production and staging; passwords stored outside Git |

Build 5 is green because the recovery rehearsal expects and verifies a failed candidate. It does not claim the deliberately bad deployment succeeded.

Evidence: http://localhost:8088/job/helpdesk/job/develop/5/ (console and archived reports). Production: http://localhost:8088/job/helpdesk/job/main/4/.

This is a local academic deployment. Jira's sprint was started today: no historical burndown has been invented. GitHub-to-Jira automatic integration and email notifications are not claimed. Prometheus/Grafana implement experiment 7; Nagios is not installed. Public webhooks are not configured because polling was explicitly selected. ShellCheck was unavailable; actual container and recovery checks are recorded above.

Docker Desktop monitoring limitation: cAdvisor currently exposes root/host CPU and memory totals, not individual container series. The dashboard labels the host fallback explicitly. API metrics and availability are application-specific.
