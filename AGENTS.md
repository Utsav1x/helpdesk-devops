# Project rules

Build an academic beginner-friendly Agile Software Development and DevOps project. The user upgraded the application to a full-stack support ticket portal. Maintain accounts, requester/agent/admin permissions, tickets, assignments, comments, dashboard and team workflows while keeping DevOps tooling central. Add short explanatory comments to every config file (use description fields for strict JSON).

Never hardcode secrets. Use .env files and Jenkins credentials. Never commit real .env files. Never use `docker system prune`, `rm -rf` outside this project, or force-push.

Work in this order and stop to verify each step: 1 Git; 2 application and at least five unit tests; 3 Docker; 4 Compose; 5 Jenkins CI; 6 deployment and rollback; 7 monitoring; 8 Jira plan; 9 documentation.

Branches: main = production; develop = staging; feature/PROJ-<n>-<short-name>. Commits: PROJ-<n>: <message>.

Run backend tests, Docker Compose config validation, Docker build/up/health/smoke/down when Docker is available, and ShellCheck when available. Fix failures. Report unavailable checks accurately and provide reproducible commands.

The user subsequently authorized setting up GitHub, Jenkins and Docker. Perform those setup actions when access permits; user authentication remains a handoff. Jira and classroom screenshots remain manual. Never claim an external setup or runtime check succeeded without evidence.
