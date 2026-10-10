# GitHub → Jenkins → deployment: beginner checklist

These are manual steps. No repository, token, job, tunnel or webhook has been created for you.

## Prepare GitHub and credentials
1. Create an empty GitHub repository. In this project run `git add .`, `git commit -m "PROJ-1: Add local CI/CD project"`, add your repository as `origin`, and push main. Create and push develop. Check `git status --ignored` before adding files; never add real env files.
2. In GitHub Settings → Developer settings → Personal access tokens → Fine-grained tokens, create an expiring token for this repository only. Give Contents read, Metadata read, and Pull requests read if PR discovery is enabled. You will create the webhook manually, so webhook write access is unnecessary. Obtain organization approval/SSO authorization if required. Copy the token once to your password manager.
3. Prepare `.env.production` and `.env.staging` using the README. Use distinct passwords and ports. Do not change a database password in the env file after first initialization without also changing the database role password.
4. Start Jenkins using `docker compose --env-file .env.production -p todo-ci -f jenkins/docker-compose.yml up -d --build --wait --wait-timeout 240`. On Linux set DOCKER_GID to `stat -c %g /var/run/docker.sock`. Docker Desktop must use Linux containers.
5. Retrieve the unlock password with `docker compose --env-file .env.production -p todo-ci -f jenkins/docker-compose.yml exec jenkins cat /var/jenkins_home/secrets/initialAdminPassword`. Open http://localhost:8088, finish the wizard and create your own admin account. Keep authentication enabled.
6. Manage Jenkins → Credentials → System → Global → Add credentials: choose Username with password; username = GitHub username; password = PAT; ID = `github-repo-read`. Do not put tokens in repository URLs.
7. Add two Secret file credentials: upload each upgraded env file (including SECRET_KEY) with IDs `todo-production-env` and `todo-staging-env`. Jenkins binds the right file only for deployment branches.

## Create the multibranch job
8. New Item → Multibranch Pipeline → name `todo`. Under Branch Sources add GitHub; choose `github-repo-read`, repository owner and repository. Discover branches. For this local socket-enabled lab, allow only trusted teammate branches; disable fork PR discovery. Anyone who can edit this Jenkinsfile can control the host through Docker.
9. Set Script Path to `Jenkinsfile`, then Save and Scan Repository Now. Confirm main and develop are discovered. The first build pulls dependencies and images and will take longer.
10. Use the built-in node for this single-machine academic demo, with at least one executor. The Jenkins image includes Python, Git, Docker CLI, Compose, Bash and curl. No Docker-in-Docker daemon is needed. Builds send contexts through the Docker API; application deployment has no workspace bind mounts, avoiding host/container path mismatches.
11. Run main and develop once. Confirm production at http://localhost:8080 and staging at http://localhost:8081. Feature branches build and test without deploying. Configure SMTP under Manage Jenkins → System if email notifications are desired, then set NOTIFY_EMAIL. Console notifications work without SMTP.

## Expose the local webhook with ngrok (optional free-tier demo)
12. Install ngrok from its official download page, create a free account, and configure your own auth token using its dashboard instructions. Do not commit its config. All services remain local; ngrok is only the temporary webhook tunnel. Free-plan limits may change. Polling below needs no tunnel or paid service.
13. Run `ngrok http 8088` in a separate terminal. Copy its HTTPS forwarding URL. Keep the terminal running. Use Jenkins' authentication and disable anonymous administrative access before exposing it.
14. Set Jenkins URL under Manage Jenkins → System to the forwarding HTTPS URL. In GitHub repository Settings → Webhooks → Add webhook, enter `https://YOUR-NGROK-HOST/github-webhook/` (trailing slash included), content type application/json, Just the push event, Active.
15. Generate a webhook secret and configure the same value in GitHub and Jenkins GitHub plugin's advanced shared-secret setting (Secret text credential). Keep this separate from the checkout PAT. If your installed plugin UI differs, consult its help for hook signature validation before exposing the endpoint.
16. In GitHub Recent deliveries check the ping and push response is 2xx. Push a README edit on develop using `PROJ-5: Verify webhook trigger`. Confirm the matching SHA appears in a new Jenkins build, with no manual Build Now click.
17. If the ngrok URL changes, update the webhook and Jenkins URL. Stop the tunnel after the demo. Rotate/revoke the demo PAT when finished.

## No-tunnel alternative: polling
18. Disable the webhook and enable the multibranch job's periodic scan trigger (for example every 1 minute during the demo, a longer interval afterward). Scanning detects changed branches without inbound connectivity. For explicit per-branch SCM polling, add `triggers { pollSCM('H/2 * * * *') }` at pipeline scope in Jenkinsfile. Run/scan once to register that trigger.
19. Push a change, wait for the configured interval and verify the build's recorded trigger. Explain that polling trades immediate delivery for periodic requests. Do not claim a polling build was webhook-triggered.

## How deployment failure is handled
`deploy.sh` validates the candidate images, snapshots both healthy running image IDs as environment-specific `:previous`, and runs Compose with `--no-build --wait`. It then performs CRUD through nginx inside the Docker network. A failure calls `rollback.sh`, which restores both images and smoke-tests them. The pipeline remains failed even when recovery succeeds. On a first deployment there is no previous version: failed app containers are removed and the DB volume is retained. Image rollback does not reverse database migrations; this project uses a fixed schema. Locks prevent concurrent deployments for one environment.

References: [Jenkins multibranch](https://www.jenkins.io/doc/book/pipeline/multibranch/), [pipeline syntax](https://www.jenkins.io/doc/book/pipeline/syntax/), [GitHub tokens](https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/managing-your-personal-access-tokens), [private webhook delivery](https://docs.github.com/en/webhooks/using-webhooks/delivering-webhooks-to-private-systems).

## Support portal first-use checklist

1. Create the first administrator with the interactive `manage.py` command in README; no staff password is hardcoded.
2. Sign in as admin and create agents under Team.
3. Register a separate requester, submit a ticket, then sign in as an agent to assign, comment and resolve.
4. The smoke gate creates a random temporary requester, tests the authenticated ticket/comment/dashboard flow and requester restrictions, then removes its own data. Run the administrator workflow manually as part of the presentation.
