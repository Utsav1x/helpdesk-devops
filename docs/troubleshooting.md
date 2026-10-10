# Troubleshooting

| Symptom | Check and fix |
|---|---|
| Docker command missing on Windows | Open a new terminal after Docker Desktop installation; use Linux containers. The executable may be under `%LOCALAPPDATA%\Programs\DockerDesktop\resources\bin`. Add that installation's bin directory to PATH. |
| Docker CLI says Access is denied | Check Windows application permissions or the automation sandbox. Running Docker Desktop does not prove a particular agent session can launch docker.exe. Try `docker version` in your own terminal; do not claim containers were tested if the CLI cannot run. |
| Jenkins cannot access Docker socket | On Linux use `stat -c %g /var/run/docker.sock`, set DOCKER_GID, and recreate Jenkins. Inspect the socket's group from inside Jenkins. Do not chmod 666 the socket. Rootful Linux Docker is the reference; rootless engines require their actual socket path. |
| Jenkins Docker commands work but mounts fail | Containers created through the socket resolve bind sources on the Docker host, not inside Jenkins. Application deployments use named DB volumes and image contents. Start monitoring from the host checkout, because its configs are bind-mounted. |
| Port is already allocated | Check `docker ps` and host listeners, adjust FRONTEND_PORT/BACKEND_PORT and monitoring/Jenkins ports in the appropriate env file. Keep distinct project names. |
| Database login fails after password edit | PostgreSQL initialization env variables apply to an empty data directory only. Restore the original password or alter the database role deliberately; do not delete the volume to hide the issue. Use hexadecimal passwords to avoid URL escaping problems. |
| Webhook does not trigger | Check GitHub Recent deliveries, tunnel availability, `/github-webhook/` spelling, signature secret, Jenkins branch discovery, and token access. Scan once manually. A feature branch intentionally does not deploy. |
| Unhealthy app containers | Run `docker compose -p todo-staging --env-file .env.staging ps` and `logs --tail=100 backend db frontend`. Check credentials, DB readiness, API route and health URL. Use docker inspect to read health probe output. |
| Grafana has no data | Wait for multiple scrapes, generate traffic, verify :9090/targets, datasource URL `http://prometheus:9090` and UID `prometheus`. Ensure monitoring uses the same project/network as the app. |
| cAdvisor metrics absent on Desktop | Read cAdvisor logs and :8082/metrics. Host paths/cgroups refer to the Linux VM and may not expose expected data. Repeat container metrics on a native Linux Docker host; do not substitute invented graphs. |
| BackendDown never fires when DB is stopped | `up` measures `/metrics` scrape reachability. Stop the backend for this alert demo. `/health` and smoke CRUD check DB readiness separately. |
| First failed deployment has no rollback version | Scripts remove failed app containers but preserve the DB. Build a good image and deploy again. A successful baseline is required for the rollback demonstration. |
| Rollback fails | Inspect previous image tags, Compose logs and DB health. Fix the underlying infrastructure issue, then run rollback manually. Reverting Git alone does not restore containers until deployment runs. |
| Bash reports bad interpreter / carriage returns | Use Git Bash or WSL on Windows, honor `.gitattributes`, and check files are LF. Run `bash scripts/deploy.sh ...` rather than relying on executable mode on Windows. `flock` is required; use WSL/Linux or Jenkins if Git Bash lacks it. |
| Vite config bundling fails under a Windows sandbox | Retry `npm run build -- --configLoader native` (Node 22+). The normal Linux Docker build uses the standard loader. |
| Plugin installation fails | Plugin dependencies resolve at build time. Check compatibility with the pinned Jenkins LTS; update/test the LTS and plugin set together. Export/pin resolved plugin versions after a successful bootstrap for stricter reproducibility. |

Keep logs in your local reports directory; redact secrets before including them in a submission. Use `docker compose down` for only this project, never `docker system prune`.
