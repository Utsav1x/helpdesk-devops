# Monitoring guide

1. Choose one environment (staging for the demo). Start the app first, then add monitoring with `docker compose -p todo-staging --env-file .env.staging -f docker-compose.yml -f docker-compose.monitoring.yml up -d --no-recreate`. Use the same project name and env file so the backend name resolves correctly. Do not run this command from Jenkins: these config bind mounts belong to the host checkout.
2. Open http://localhost:9090/targets and verify backend, cadvisor and prometheus are UP. Open http://localhost:3000 and sign in with the credentials in your env file. Open Dashboards → DevOps → DevOps pipeline overview.
3. Run `bash scripts/load-test.sh http://localhost:8081 300`. Wait for at least two scrapes; p95 becomes meaningful with requests over the five-minute window. Health traffic is excluded from API panels.
4. For the alert demo, run `docker compose -p todo-staging --env-file .env.staging stop backend`. Wait roughly 70–90 seconds and open http://localhost:9090/alerts. BackendDown should be firing. Restart with `docker compose -p todo-staging --env-file .env.staging start backend` and confirm recovery. Alerts are displayed locally; no Alertmanager/email delivery is configured.
5. Screenshot targets, all five panels and the firing alert. Avoid displaying passwords or credential pages.
6. Stop the merged stack with the same two `-f` arguments and `down`. Never add `-v` unless intentionally deleting demo data.

## Panel queries

### Container CPU (%)

```promql
100 * sum by (name) (rate(container_cpu_usage_seconds_total{job="cadvisor",image!=""}[2m]))
```

### Container memory

```promql
sum by (name) (container_memory_working_set_bytes{job="cadvisor",image!=""})
```

### API request rate

```promql
sum(rate(http_requests_total{job="backend",route!="/health"}[2m]))
```

### API p95 latency

```promql
histogram_quantile(0.95, sum by (le) (rate(http_request_duration_seconds_bucket{job="backend",route!="/health"}[5m])))
```

### Backend scrape up/down

```promql
up{job="backend"}
```

CPU is percent of one core; a multicore container can exceed 100%. Memory is working-set bytes. The p95 is estimated from histogram buckets, not an average. `up` confirms Prometheus reached `/metrics`; database availability is checked by `/health` and CRUD smoke tests. cAdvisor panels show all containers visible to the local engine.

Docker Desktop runs containers inside a Linux VM. cAdvisor filesystem mounts, CPU and memory visibility vary by Desktop/WSL/cgroup version. If those panels are empty, inspect cAdvisor logs and its `/metrics`; a native Linux Docker host is the reference environment. The backend panels remain useful independently.

To monitor both environments simultaneously, start a monitoring stack for each and assign different PROMETHEUS_PORT, GRAFANA_PORT and CADVISOR_PORT values in their env files. Each has its own datasource and app network.

References: [Compose startup ordering](https://docs.docker.com/compose/how-tos/startup-order/), [Prometheus histograms](https://prometheus.io/docs/practices/histograms/).
