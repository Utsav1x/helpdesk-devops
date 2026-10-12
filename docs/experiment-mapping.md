# Experiment mapping

| Experiment | Topic | Exact project files | Evidence to demonstrate |
|---|---|---|---|
| 1 | Git | `.gitignore`, `.gitattributes`, `AGENTS.md`, `README.md` Git workflow | feature branch, PROJ commit, reviewed PR, conflict resolution, release tag |
| 2 | Docker | `backend/Dockerfile`, `backend/.dockerignore`, `frontend/Dockerfile`, `frontend/.dockerignore` | multi-stage build, pinned images, non-root app users, health checks |
| 3 | Docker Compose | `docker-compose.yml`, `.env.example` | separate project networks/volumes, health-dependent startup, two environments |
| 4 | Jenkins CI | `Jenkinsfile`, `jenkins/Dockerfile`, `jenkins/docker-compose.yml`, `jenkins/plugins.txt`, `backend/tests/test_app.py`, `backend/portal.py` | stages, passing unit report, archived artifacts, notifications |
| 5 | Automated CD | `scripts/common.sh`, `scripts/deploy.sh`, `scripts/rollback.sh`, `scripts/smoke-test.sh`, `scripts/smoke.py`, `docs/github-jenkins-setup.md`, `docs/demo-script.md` | push-triggered deployment, branch rules, failed smoke and previous-image recovery |
| 6 | Jira / Scrum | `docs/jira-plan.md` | HDEV-3 epic, nine stories, active sprint, status board, example estimate/owner/acceptance criteria; no fabricated historical burndown |
| 7 | Monitoring | `docker-compose.monitoring.yml`, `monitoring/prometheus.yml`, `monitoring/alert.rules.yml`, `monitoring/grafana/provisioning/datasources/prometheus.yml`, `monitoring/grafana/provisioning/dashboards/default.yml`, `monitoring/grafana/dashboards/overview.json`, `scripts/load-test.sh`, `scripts/load.py`, `docs/monitoring.md` | targets, five panels, generated load, BackendDown alert |

The website is the actual artifact these experiments deliver: requester/agent/admin accounts, a ticket queue, assignment and replies, dashboard metrics and team management. Product dashboard figures come from the application database; infrastructure graphs come separately from Prometheus/Grafana. No in-app badge pretends a Jenkins build or deployment has succeeded.
