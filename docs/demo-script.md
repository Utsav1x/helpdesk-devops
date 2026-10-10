# Five-minute live demo

## Successful delivery
1. Before presenting: finish the GitHub/Jenkins checklist, warm image caches, ensure develop has a successful baseline, and start monitoring. Open GitHub deliveries, Jenkins, staging at :8081 and Grafana at :3000. This preparation is outside the five minutes.
2. 0:00–0:45: show the architecture and Jira story PROJ-5. Edit the heading in `frontend/src/Portal.jsx` on `feature/PROJ-5-demo`. Commit `PROJ-5: Update demo heading`, push, and show its PR into develop.
3. 0:45–1:15: merge the reviewed PR into develop. Show GitHub's push webhook delivery and its 2xx response.
4. 1:15–3:00: open the automatically started Jenkins build. Explain checkout, dependencies, unit reports, image build, deployment and smoke gate. Actual time depends on cache and laptop speed; do not promise a cold build completes in five minutes.
5. 3:00–4:00: show `docker compose -p todo-staging --env-file .env.staging ps` and `docker compose -p todo-staging --env-file .env.staging images`. Refresh :8081, show the new heading and create a ticket, assign it, add a reply and mark it resolved.
6. 4:00–5:00: run `bash scripts/load-test.sh http://localhost:8081 100`. Show Grafana request rate and p95 latency (allow the scrape/rate window to populate), then the Jira story's acceptance criteria and test report.

## Second scenario: smoke failure and automatic rollback
1. Keep this exercise on staging. Record the current backend/frontend image IDs and the visible heading. Confirm a successful baseline exists before breaking anything.
2. On a new feature branch change nginx's `location /api/` body to `return 503;`, leaving `/health` and the root page unchanged. This simulates an integration routing defect that backend unit tests cannot catch.
3. Commit `PROJ-5: Demonstrate staging proxy regression`, push and merge into develop after explaining that this is a deliberate teaching exercise.
4. Watch backend tests and image builds pass. Container health checks also pass. The deployment's CRUD smoke test receives 503, causing deploy.sh to call rollback.sh.
5. Show the failed build, the explicit rollback output, the restored image IDs (`:previous` tags point to the old IDs), and working CRUD at :8081. A successful recovery does not turn the failed candidate build green.
6. Revert the broken commit with `git revert <broken-commit>` (or `git revert -m 1 <merge-commit>` for a merge), then push. Confirm the next deployment succeeds. Never force-push. If rollback itself fails, inspect logs and repair manually; do not claim recovery occurred.
