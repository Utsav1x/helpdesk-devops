# Scrum plan (manual Jira setup)

Epic PROJ-10: Deliver a repeatable, observable local web application pipeline.

Three one-week sprints; story points estimate relative effort. Definition of Done: acceptance criteria pass, teammate review complete, documentation updated, evidence saved, no secrets committed. Bugs below are proposed teaching scenarios, not claims of observed defects.

| Sprint / goal | Story | Points | Acceptance criteria | Tasks |
|---|---|---:|---|---|
| 1: working app and containers | PROJ-1 Git workflow | 2 | main/develop/feature workflow documented; sample conflict resolved on a practice branch | initialize repo; ignore secrets; PR review |
| 1 | PROJ-2 Authenticated ticket API | 5 | Ticket CRUD/comments persist; requester isolation and staff permissions pass; 32 tests pass | Flask routes; SQLAlchemy; pytest |
| 1 | PROJ-3 React frontend | 3 | login, dashboard, ticket search/filter, assignment, comments and team screens work; errors visible | responsive portal; auth/session state; proxy; production build |
| 1 | PROJ-4 Container environments | 5 | healthy services; named DB volume survives down/up; staging ports do not collide | Dockerfiles; Compose; env templates |
| 2: automated delivery and recovery | PROJ-5 Jenkins webhook delivery | 8 | push triggers build; develop stages; main produces production; feature branches never deploy | Jenkins image/plugins; job; webhook; credentials |
| 2 | PROJ-6 Smoke gate and rollback | 5 | failed candidate restores old app images and fails build; first failure retains DB | scripts; lock; integration failure demo |
| 3: observable and documented demo | PROJ-7 Metrics and dashboard | 5 | three scrape targets; five panels; BackendDown fires after 1 minute | Prometheus; provisioning; load loop |
| 3 | PROJ-8 Agile evidence | 2 | board, backlog, burndown and ticket/commit links captured | Jira setup; sprint updates; screenshots |
| 3 | PROJ-9 Final documentation | 3 | fresh-clone checklist, seven experiment mappings, 20 viva answers and demo available | README; troubleshooting; rehearse |

## Sample sprint backlog
| Sprint | Item | Owner role | Status | Estimate |
|---|---|---|---|---:|
| 2 | PROJ-5 Jenkins image + credentials | CI owner | To Do | 3 tasks |
| 2 | PROJ-5 GitHub hook and branch test | Git owner | To Do | 2 tasks |
| 2 | PROJ-6 Snapshot + rollback scripts | Deployment owner | To Do | 2 tasks |
| 2 | PROJ-6 Broken nginx smoke demo | Tester | To Do | 1 task |

## Bug backlog
| Suggested key | Sprint | Reproduction | Expected fix / acceptance |
|---|---|---|---|
| PROJ-11 | 1 | Submit whitespace-only title | Reject with HTTP 400; regression test passes |
| PROJ-12 | 2 | Deploy nginx with API route returning 503 | Smoke fails; previous images restored; build stays red |
| PROJ-13 | 3 | Set wrong Prometheus datasource URL | Restore service DNS URL; targets and panels recover |

## Numbered Jira setup checklist
1. Create a Scrum project with key PROJ, using an available free Jira plan for the academic team. Product setup is done by you; the application/pipeline itself does not depend on Jira or any paid service.
2. Add the epic and nine stories above. Jira assigns actual issue numbers; if they differ from the suggested keys, update branch/commit examples to the real keys. Add acceptance criteria to Description and task rows as subtasks.
3. Create three sprints with the goals above. Add story points to stories, not both stories and their subtasks (avoid double-counting). Assign team roles and agree sprint capacity.
4. Put stories in their sprint and start Sprint 1. During daily check-ins move work To Do → In Progress → Done only when Definition of Done passes. Hold a review and retrospective at each sprint end.
5. Connect GitHub through Jira's repository integration if available to your account. Create branches like `feature/PROJ-2-todo-api`, commits like `PROJ-2: Validate task titles`, and PR titles like `PROJ-2: Add CRUD endpoints`. Key references work as text even without an integration; automatic links require one.
6. Where Smart Commits are enabled, use `PROJ-2 #comment Backend tests passed #time 30m`. Transition examples such as `PROJ-2 #done` depend on workflow transition names and permissions; verify on a test issue. Git author email must match the Jira account. Ordinary `PROJ-2:` commits do not automatically transition an issue.
7. To capture the board, open Active sprint, show issue keys and statuses, and save a screenshot without account secrets. Use a consistent browser zoom so all columns are visible.
8. To capture burndown, open Reports → Burndown, select the actual sprint and story-point estimation. Record progress over several days; do not fabricate a historical chart. Capture the report after at least one completed story and explain any scope change.
9. Capture backlog, epic and one story with acceptance criteria and linked PR. Add screenshots to your academic submission, not confidential tokens or personal account settings.
