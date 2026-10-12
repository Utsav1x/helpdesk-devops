# Teacher presentation: Helpdesk DevOps

Say: “This is a full-stack support ticket website delivered through a DevOps pipeline. Git tracks changes, Docker packages it, Compose runs its services, Jenkins tests and deploys it, Jira tracks the work, and Prometheus/Grafana monitor it.”

Keep Docker Desktop running. These localhost links work on this computer while the containers are running.
Passwords are in the separate private login guide supplied locally; do not put that file in GitHub or your submission.

| Open | Login | Demonstrate |
|---|---|---|
| [Production portal](http://localhost:8080) | presenter@helpdesk.local | Create a ticket, select priority, add a comment; show dashboard and Team |
| [Staging portal](http://localhost:8081) | presenter@helpdesk.local | Separate deployment/database for develop branch |
| [GitHub repository](https://github.com/gokhale-atharva/helpdesk-devops) | Your existing gokhale-atharva account | main/develop, PRs 1 and 2, Dockerfiles, Compose, Jenkinsfile |
| [Conflict exercise](https://github.com/gokhale-atharva/helpdesk-devops/tree/exercise/git-conflict-resolved) | GitHub account | Actual merge commit preserving both edits |
| [Release tag](https://github.com/gokhale-atharva/helpdesk-devops/tree/v1.0.0-demo) | GitHub account | Reproducible released code |
| [Jenkins pipeline](http://localhost:8088/job/helpdesk/) | helpdesk-admin | Branch jobs and stage results |
| [Production build 4](http://localhost:8088/job/helpdesk/job/main/4/) | helpdesk-admin | Successful production delivery |
| [Recovery rehearsal build 5](http://localhost:8088/job/helpdesk/job/develop/5/) | helpdesk-admin | 32 tests, Docker deployment, persistence, rollback and alert recovery |
| [Jenkins test results](http://localhost:8088/job/helpdesk/job/develop/5/testReport/) | helpdesk-admin | Passing test suite |
| [Jira board](https://atharvagokhale.atlassian.net/jira/software/projects/HDEV/boards/36) | Your existing Atlassian account | Eight Done stories and presentation In Progress |
| [Jira acceptance criteria](https://atharvagokhale.atlassian.net/browse/HDEV-9) | Atlassian account | Owner, estimate, epic and criteria |
| [Grafana dashboard](http://localhost:3000/d/devops-overview/devops-pipeline-overview) | admin | Container CPU/memory, request rate, latency and availability |
| [Prometheus targets](http://localhost:9090/targets) | No login | Three UP scrape targets |
| [Prometheus alerts](http://localhost:9090/alerts) | No login | BackendDown rule; saved firing/recovery JSON in evidence folder |
| [cAdvisor](http://localhost:8082) | No login | Container resource metrics |

## Seven experiments, in order

1. Git: show branches, merged PRs, resolved-conflict branch and release tag.
2. Docker: open backend/Dockerfile and frontend/Dockerfile; show images/healthy containers in Docker Desktop.
3. Compose: show docker-compose.yml and the frontend/backend/PostgreSQL services, separate staging/production projects and DB volumes. Persistence rehearsal passed.
4. Jenkins: open develop build 5, stage view, 32-test report and console.
5. Automated deployment: explain the one-minute GitHub repository scan. main deploys 8080; develop deploys 8081. Show the archived rehearsal.txt: failed candidate, restored previous images, working API. The harness is green because it verified the expected failure and recovery.
6. Jira: show active sprint, work statuses and HDEV-9 details. This sprint began today; do not present invented historical burndown.
7. Monitoring: show targets UP and Grafana panels; show alert-firing.json and alert-recovered.json from the controlled outage. Nagios is not needed for this chosen Prometheus/Grafana implementation.

## Repeat a recovery demonstration

In Jenkins → helpdesk → develop → Build with Parameters, select REHEARSE_STAGING and build. This briefly interrupts staging and intentionally deploys a bad candidate before rollback. Use the saved successful build 5 for a fast classroom presentation. Production remains separate.

The remaining human step is your classroom review/presentation (HDEV-10), not application implementation. No webhook relay or invented sprint history is required.

Docker Desktop monitoring limitation: cAdvisor currently exposes root/host CPU and memory totals, not individual container series. The dashboard labels the host fallback explicitly. API metrics and availability are application-specific.
