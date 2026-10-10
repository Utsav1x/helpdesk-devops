# GitHub and Jenkins first-run setup

This launcher is prepared for a fresh local Jenkins installation. It has passed static checks; Docker runtime verification is still pending. It refuses to replace existing Jenkins users. Use the [manual setup guide](github-jenkins-setup.md) for an existing Jenkins installation.

1. Start Docker Desktop using Linux containers. Confirm `docker version` reports both client and server.
2. Authorize GitHub CLI with `gh auth login`. Create a private repository you administer and push the project with both `main` and `develop` branches. Never push the private environment files.
3. From the project directory, run:

```powershell
powershell -NoProfile -File .\scripts\complete-setup.ps1 -Repository YOUR-ACCOUNT/helpdesk-devops
```

If GitHub CLI was authorized with a separate configuration directory, add `-GitHubConfig` followed by its absolute path. Python and GitHub CLI must be on PATH.

The launcher verifies GitHub access, prepares ignored `.bootstrap` inputs, stops this project's SQLite preview to free port 8081, validates Compose, and starts Jenkins. It waits for the bootstrap marker and HTTP login page before reporting completion. Image download/build time may be several minutes.

Open http://localhost:8088/job/helpdesk/. Sign in as `helpdesk-admin` with the password in `.bootstrap/jenkins-admin-password.txt`. Keep that file private. Jenkins imports GitHub credentials and the two environment files, scans branches, and runs the pipeline: tests, images, deployment and authenticated smoke test. `main` deploys to http://localhost:8080 and `develop` to http://localhost:8081. Other branches build without deployment. A successful bootstrap is not yet a successful pipeline: wait for green branch builds and inspect their logs and test reports.

This setup uses periodic repository scanning every minute. **It does not configure a public GitHub webhook.** The manual guide explains the separate webhook/tunnel setup if your experiment requires a webhook delivery screenshot.

For the classroom demonstration, show the GitHub commit, matching Jenkins checkout SHA, green stages/test report, healthy containers in Docker Desktop, and the deployed ticket portal. Create the first administrator using the interactive `backend/manage.py` command in the README. Push a small visible change to `develop`, wait for the next scan/build, and show the updated staging website.

If startup fails, inspect this project's Jenkins logs:

```powershell
docker compose -p todo-ci --env-file .env.production -f jenkins/docker-compose.yml -f jenkins/docker-compose.bootstrap.yml logs --tail 100 jenkins
```

Do not delete Jenkins volumes to retry: they hold credentials and build history. If bootstrap stopped after creating the administrator, use its saved password and finish through the manual guide. Never share `.bootstrap`, real `.env` files or GitHub CLI authentication files. They are excluded from Git and the project ZIP.
