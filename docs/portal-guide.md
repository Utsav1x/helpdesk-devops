# Helpdesk support portal

## Application demonstration
1. Open the local preview and choose Explore the sample workspace. This signs in to a clearly labelled fictional workspace as Maya Chen, an administrator. Production deployments have no sample sign-in; create a real admin with manage.py.
2. On Overview, explain that ticket counts, activity charts and priority distribution are calculated from stored tickets. They are product reports, separate from infrastructure monitoring in Grafana.
3. Select New ticket. Enter a subject, category, priority and description. Submit and note its HD- number.
4. In Ticket properties choose an agent, change status to In progress, and add a reply in Conversation. Verify the history records each change.
5. Return to All tickets. Search by title/ID/requester, try status tabs and the priority filter. Open the same ticket and resolve it. Check Reports and the agent's workload on Team.
6. Sign out and register a requester account using your own test details. Only that requester's tickets should appear. Requesters cannot assign or resolve tickets and cannot create agents. Sign out and return to the sample workspace when using the preview.
7. For an actual Docker deployment, bootstrap the admin with `docker compose -p todo-staging --env-file .env.staging exec backend python manage.py`. Add agents in Team. Then repeat steps 2–6 with real local test accounts.

## Roles
| Capability | Requester | Agent | Administrator |
|---|---|---|---|
| Submit ticket | Yes | Yes | Yes |
| View/edit/comment | Own tickets | All tickets | All tickets |
| Assign/change status | No | Yes | Yes |
| Delete ticket | Own tickets | Own tickets | All tickets |
| Add support agents | No | No | Yes |

## How the experiments use this website
- Git branches and PROJ commits carry changes to the portal.
- Docker packages React/nginx, Flask and PostgreSQL.
- Compose isolates staging and production databases, networks and ports.
- Jenkins runs the permission/workflow tests and builds images.
- GitHub pushes initiate eligible deployments. The smoke test creates a random temporary requester and exercises ticket operations through nginx; failure invokes rollback.
- Jira stories track account, ticket, interface, pipeline and observability work.
- Prometheus captures HTTP request counts/durations; Grafana displays infrastructure/API panels and cAdvisor supplies container resource metrics.

The product has no pretend deployment-success indicator. A working portal proves the application path; only a real Jenkins build, container inspection and rollback test establish the DevOps pipeline.

## Data and security boundaries
Passwords are hashed; signed session cookies are HttpOnly and SameSite=Lax, with CSRF checks on API mutations. SECRET_KEY must remain private and stable between releases. Use COOKIE_SECURE=true behind HTTPS. Public registration always creates requester accounts. The demo has no email delivery, attachments, password-reset service, MFA or distributed brute-force throttling; keep the academic deployment local.

Resolution targets are 4/24/48/72 hours for urgent/high/medium/low, measured from ticket creation. Changing priority recalculates the target; unresolved tickets past that time count as overdue. These are application targets, not contractual SLA guarantees.
