# Twenty viva questions

1. **What is CI?** Automatically building and testing each integrated code change.
2. **What is CD?** Continuous delivery prepares validated releases; continuous deployment also releases automatically. This project's trusted main/develop branches deploy automatically.
3. **Why a support portal?** It provides real multi-user workflows (requesters, agents, tickets and replies) whose permissions and integration can be tested by the DevOps pipeline.
4. **Why use feature branches?** To isolate one story for review before integration into develop and promotion to main.
5. **How do you resolve a merge conflict?** Inspect both changes, edit the intended result, stage and commit; rerun relevant checks.
6. **Image versus container?** An image is a packaged filesystem and configuration; a container is a running instance with its own writable layer.
7. **Why multi-stage builds?** Build tools stay outside the final runtime image, reducing size and unnecessary dependencies.
8. **Why non-root users?** They reduce application privileges within the container; Docker socket access is a separate host-level privilege.
9. **What does Compose provide?** Declarative service, network, volume and startup configuration for a local multi-container system.
10. **Why a named database volume?** Data survives container replacement and ordinary compose down; down -v intentionally deletes it.
11. **Does depends_on guarantee readiness?** Only a dependency marked service_healthy waits for its health check; it does not guarantee future uptime.
12. **How are environments separated?** Distinct project names give separate networks and volumes; env files set separate ports and credentials.
13. **What is a Jenkins multibranch job?** It discovers branches with a Jenkinsfile and runs a pipeline for each under branch-specific rules.
14. **Webhook versus polling?** A webhook sends an event immediately; polling periodically asks the SCM for changes and needs no inbound tunnel.
15. **Where are secrets kept?** Ignored local env files and Jenkins credentials; real secrets are not part of Git or Docker images.
16. **Why unit and smoke tests?** Unit tests check API behavior in isolation; smoke tests check actual nginx/API/database integration after deployment.
17. **How does rollback work?** Running image IDs receive environment-specific previous tags before deployment. Failure recreates the app from those images and verifies recovery.
18. **What cannot image rollback repair?** Incompatible database migrations, lost data, broken host infrastructure, or missing previous images. This project has no destructive migrations.
19. **How is p95 latency calculated?** Prometheus applies histogram_quantile to rates of request-duration buckets; it estimates the latency under which 95% of observations fall.
20. **What do Scrum artifacts and monitoring contribute?** Backlog/sprints make work and acceptance visible; dashboards and alerts make runtime behavior visible after release.
