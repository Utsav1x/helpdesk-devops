# Support portal verification — 10 October 2026

The earlier To-Do application has been replaced by a full-stack support portal. Existing database volumes and legacy tables were preserved. The old verification record is superseded by the checks below.

| Check actually executed | Result |
|---|---|
| Backend unit/integration tests in a fresh pinned dependency environment | **32 passed in 10.64s**; JUnit report written to reports/unit-tests.xml |
| Access controls | Tests cover session/CSRF checks, requester isolation, forbidden staff actions, assignment validation and administrator-only agent creation |
| Ticket workflows | Tests cover CRUD, comments, activity, cascading deletion, dashboard counts and temporary account cleanup |
| React production build | Passed with `npm run build -- --configLoader native`; 22 modules transformed |
| Real local HTTP smoke test | Passed against the running Flask/SQLite portal: index, registration, cookie/CSRF session, ticket CRUD, comment, dashboard, requester permission boundary and cleanup |
| Authenticated load generator | Completed 10 requests; removed its temporary requester afterward |
| Browser workflow | Sample workspace opened; a ticket was submitted, assigned to Alex Morgan, replied to and resolved; saved changes appeared in the interface |
| Configuration checks | Compose/monitoring YAML parsed; Bash syntax checked; PowerShell launcher parsed |
| Secret-file upgrade | Added missing random SECRET_KEY to existing ignored env files while preserving database/Grafana passwords |

The browser sample is served by `backend/preview.py` on loopback port 8081. It uses fictional sample data in `.preview/support.db`. The demo-login endpoint is enabled only by this preview launcher, not by the production application factory. The container image copies app.py, portal.py and manage.py only. No demo user password is hardcoded.

## Still unverified

Docker Desktop is installed and was previously found running under `%LOCALAPPDATA%\Programs\DockerDesktop`. Launching its CLI from this Codex session returned **Access is denied**. This upgrade does not claim to have resolved that restriction.

Docker Compose semantic validation, image builds, PostgreSQL container integration, Jenkins execution/plugin installation, GitHub-triggered deployment, real image rollback, promtool, Grafana provisioning and cAdvisor metrics remain **unverified**. Parsing YAML does not replace `docker compose config`. ShellCheck/flock were not available in the Git Bash environment; syntax checks do not prove lock behavior. The full deployment and rollback demo must be rehearsed on an accessible Docker engine.

GitHub device authorization and Docker access are pending. A first-run Jenkins bootstrap now prepares credentials and a multibranch job with one-minute repository polling; its Python and PowerShell syntax and YAML structure passed static checks, but it has not run in Docker. GitHub publication, Jenkins builds and container deployment are not yet verified. Public webhook/ngrok, Jira setup and classroom screenshots remain outstanding. Product dashboard data is real application data; it is not evidence that Jenkins or monitoring has run.

## Reproduce locally

For the website preview, see README → Local website preview. For the full application containers, stop the preview first so port 8081 is free, then run from the repository root:

```powershell
powershell -NoProfile -File .\scripts\demo.ps1
```

The launcher locates Docker, validates Compose, builds staging, waits for healthy containers, and runs the authenticated HTTP smoke test. To add monitoring and Jenkins:

```powershell
powershell -NoProfile -File .\scripts\demo.ps1 -Monitoring -Jenkins
```

Create your first admin using the interactive manage.py command in README. Upgrade/re-upload both Jenkins secret env files to include SECRET_KEY. Rehearse the success and failure scenarios in docs/demo-script.md. Stop with the same launcher flags plus `-Stop`; volumes persist.

Explicit remaining validation commands:

```bash
python scripts/init-env.py
docker version
docker compose -p todo-production --env-file .env.production config --quiet
docker compose -p todo-staging --env-file .env.staging config --quiet
docker compose -p todo-staging --env-file .env.staging -f docker-compose.yml -f docker-compose.monitoring.yml config --quiet
docker compose -p todo-ci --env-file .env.production -f jenkins/docker-compose.yml config --quiet
docker compose -p todo-production --env-file .env.production up -d --build --wait --wait-timeout 180
python scripts/smoke.py http://localhost:8080
docker compose -p todo-production --env-file .env.production down
shellcheck -x scripts/common.sh scripts/deploy.sh scripts/rollback.sh scripts/smoke-test.sh scripts/load-test.sh
```

Install ShellCheck if needed. The backend image uses Python 3.12 on Linux; local tests used Python 3.13 on Windows. Runtime parity requires the pending container checks. The frontend uses system font fallbacks with no external font service required.
