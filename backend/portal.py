"""Helpdesk API with role-scoped tickets and cookie-based authentication."""
import os
import secrets
import time
from datetime import datetime, timedelta, timezone
from functools import wraps
from flask import Flask, g, jsonify, request, session
from prometheus_client import CollectorRegistry, Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST
from sqlalchemy import Column, ForeignKey, Integer, MetaData, String, Table, Text, create_engine, event, select, text
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from werkzeug.security import check_password_hash, generate_password_hash

STATUSES = ('open', 'in_progress', 'waiting', 'resolved')
PRIORITIES = ('low', 'medium', 'high', 'urgent')
CATEGORIES = ('General', 'Account access', 'Hardware', 'Software', 'Network', 'Billing')
SLA_HOURS = {'low': 72, 'medium': 48, 'high': 24, 'urgent': 4}

def now():
    return datetime.now(timezone.utc).isoformat()

def create_app(database_url=None, secret_key=None):
    app = Flask(__name__)
    key = secret_key or os.environ.get('SECRET_KEY')
    if not key or len(key) < 32:
        raise RuntimeError('Set SECRET_KEY to at least 32 random characters')
    app.config.update(SECRET_KEY=key, MAX_CONTENT_LENGTH=64*1024, SESSION_COOKIE_HTTPONLY=True,
                      SESSION_COOKIE_SAMESITE='Lax', PERMANENT_SESSION_LIFETIME=timedelta(hours=8),
                      SESSION_COOKIE_SECURE=os.environ.get('COOKIE_SECURE', 'false').lower() == 'true')
    engine = create_engine(database_url or os.environ['DATABASE_URL'], pool_pre_ping=True)
    if engine.dialect.name == 'sqlite':
        @event.listens_for(engine, 'connect')
        def foreign_keys(connection, _):
            connection.execute('PRAGMA foreign_keys=ON')
    meta = MetaData()
    users = Table('support_users', meta, Column('id', Integer, primary_key=True),
        Column('name', String(80), nullable=False), Column('email', String(200), nullable=False, unique=True),
        Column('password_hash', String(256), nullable=False), Column('role', String(20), nullable=False),
        Column('created_at', String(40), nullable=False))
    tickets = Table('support_tickets', meta, Column('id', Integer, primary_key=True),
        Column('title', String(160), nullable=False), Column('description', Text, nullable=False),
        Column('status', String(20), nullable=False), Column('priority', String(20), nullable=False),
        Column('category', String(40), nullable=False), Column('requester_id', ForeignKey('support_users.id'), nullable=False),
        Column('assignee_id', ForeignKey('support_users.id')), Column('created_at', String(40), nullable=False),
        Column('updated_at', String(40), nullable=False), Column('due_at', String(40), nullable=False),
        Column('resolved_at', String(40)))
    comments = Table('support_comments', meta, Column('id', Integer, primary_key=True),
        Column('ticket_id', ForeignKey('support_tickets.id', ondelete='CASCADE'), nullable=False),
        Column('author_id', ForeignKey('support_users.id'), nullable=False), Column('body', Text, nullable=False),
        Column('created_at', String(40), nullable=False))
    activities = Table('support_activity', meta, Column('id', Integer, primary_key=True),
        Column('ticket_id', ForeignKey('support_tickets.id', ondelete='CASCADE'), nullable=False),
        Column('actor_id', ForeignKey('support_users.id'), nullable=False), Column('message', String(240), nullable=False),
        Column('created_at', String(40), nullable=False))
    # Separate tables preserve legacy To-Do data; no destructive migration is needed.
    meta.create_all(engine)
    app.extensions.update(db=engine, tables=dict(users=users, tickets=tickets, comments=comments, activities=activities))
    registry = CollectorRegistry()
    count = Counter('http_requests_total', 'API requests', ['method','route','status'], registry=registry)
    latency = Histogram('http_request_duration_seconds', 'API latency', ['method','route'], registry=registry)

    @app.before_request
    def prepare():
        g.started = time.perf_counter()
        g.user = None
        if request.path.startswith('/api/'):
            session.setdefault('csrf', secrets.token_hex(24))
            if request.method in ('POST','PATCH','DELETE','PUT') and not secrets.compare_digest(request.headers.get('X-CSRF-Token',''), session['csrf']):
                return jsonify(error='Invalid security token. Refresh and try again.'), 403
            if session.get('user_id'):
                with engine.connect() as conn:
                    g.user = conn.execute(select(users).where(users.c.id == session['user_id'])).mappings().first()

    @app.after_request
    def record(response):
        if request.path != '/metrics':
            route = request.url_rule.rule if request.url_rule else 'unmatched'
            count.labels(request.method, route, str(response.status_code)).inc()
            latency.labels(request.method, route).observe(time.perf_counter()-g.started)
        if request.path.startswith('/api/'):
            response.headers['Cache-Control'] = 'no-store'
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['X-Frame-Options'] = 'DENY'
        return response

    @app.errorhandler(SQLAlchemyError)
    def database_error(error):
        app.logger.error('Database operation failed: %s', type(error).__name__)
        return jsonify(error='Database unavailable'), 503

    def auth(view):
        @wraps(view)
        def wrapped(*args, **kwargs):
            if not g.user:
                return jsonify(error='Please sign in'), 401
            return view(*args, **kwargs)
        return wrapped

    def public(row):
        return {key: row[key] for key in ('id','name','email','role')}

    def body():
        value = request.get_json(silent=True)
        return value if isinstance(value, dict) else {}

    def string(value, maximum, minimum=1):
        return isinstance(value, str) and minimum <= len(value.strip()) <= maximum

    def scope():
        return tickets.c.requester_id == g.user['id'] if g.user['role'] == 'requester' else text('1=1')

    def find(conn, ticket_id):
        return conn.execute(select(tickets).where(tickets.c.id == ticket_id, scope())).mappings().first()

    def enrich(conn, rows):
        people = {row.id:row.name for row in conn.execute(select(users.c.id, users.c.name))}
        return [dict(row, key=f'HD-{1000+row["id"]}', requester=people[row['requester_id']],
                     assignee=people.get(row['assignee_id']), overdue=row['status'] != 'resolved' and row['due_at'] < now()) for row in rows]

    def audit(conn, ticket_id, message):
        conn.execute(activities.insert().values(ticket_id=ticket_id, actor_id=g.user['id'], message=message, created_at=now()))

    def signed_in(row):
        session.clear()
        session.update(user_id=row['id'], csrf=secrets.token_hex(24))
        session.permanent = True
        return jsonify(user=public(row), csrf=session['csrf'], demo=bool(app.config.get('DEMO_USER_ID')))

    @app.get('/health')
    def health():
        with engine.connect() as conn:
            conn.execute(text('SELECT 1'))
        return jsonify(status='ok')

    @app.get('/metrics')
    def metrics():
        return app.response_class(generate_latest(registry), mimetype=CONTENT_TYPE_LATEST)

    @app.get('/api/session')
    def get_session():
        return jsonify(user=public(g.user) if g.user else None, csrf=session['csrf'], demo=bool(app.config.get('DEMO_USER_ID')))

    @app.post('/api/auth/register')
    def register():
        data = body()
        if set(data)-{'name','email','password'} or not string(data.get('name'),80) or not string(data.get('email'),200) or '@' not in data['email'] or not string(data.get('password'),128,10):
            return jsonify(error='Enter a name, email and a password of 10–128 characters.'), 400
        try:
            with engine.begin() as conn:
                result = conn.execute(users.insert().values(name=data['name'].strip(), email=data['email'].strip().lower(),
                    password_hash=generate_password_hash(data['password']), role='requester', created_at=now()))
                row = conn.execute(select(users).where(users.c.id == result.inserted_primary_key[0])).mappings().one()
        except IntegrityError:
            return jsonify(error='An account with that email already exists'), 409
        response = signed_in(row)
        response.status_code = 201
        return response

    @app.post('/api/auth/login')
    def login():
        data = body()
        if not string(data.get('email'),200) or not string(data.get('password'),128):
            return jsonify(error='Enter your email and password'), 400
        with engine.connect() as conn:
            row = conn.execute(select(users).where(users.c.email == data['email'].strip().lower())).mappings().first()
        if not row or not check_password_hash(row['password_hash'], data['password']):
            return jsonify(error='Email or password is incorrect'), 401
        return signed_in(row)

    @app.post('/api/auth/demo')
    def demo():
        # Enabled by the separate local preview launcher only, never by production env files.
        if not app.config.get('DEMO_USER_ID'):
            return jsonify(error='Demo workspace is disabled'), 404
        with engine.connect() as conn:
            row = conn.execute(select(users).where(users.c.id == app.config['DEMO_USER_ID'])).mappings().one()
        return signed_in(row)

    @app.post('/api/auth/logout')
    def logout():
        session.clear()
        session['csrf'] = secrets.token_hex(24)
        return jsonify(csrf=session['csrf'])

    @app.delete('/api/account')
    @auth
    def delete_account():
        if g.user['role'] != 'requester':
            return jsonify(error='Staff accounts cannot be self-deleted'), 403
        with engine.begin() as conn:
            if conn.execute(select(tickets.c.id).where(tickets.c.requester_id == g.user['id'])).first():
                return jsonify(error='Delete your tickets before deleting your account'), 409
            conn.execute(comments.delete().where(comments.c.author_id == g.user['id']))
            conn.execute(activities.delete().where(activities.c.actor_id == g.user['id']))
            conn.execute(users.delete().where(users.c.id == g.user['id']))
        session.clear()
        return '', 204

    @app.get('/api/team')
    @auth
    def team():
        with engine.connect() as conn:
            return jsonify([public(row) for row in conn.execute(select(users).where(users.c.role.in_(['admin','agent'])).order_by(users.c.name)).mappings()])

    @app.post('/api/team')
    @auth
    def add_agent():
        if g.user['role'] != 'admin':
            return jsonify(error='Administrator access required'), 403
        data = body()
        if not string(data.get('name'),80) or not string(data.get('email'),200) or '@' not in data['email'] or not string(data.get('password'),128,10):
            return jsonify(error='Provide name, email and a password of 10–128 characters'), 400
        try:
            with engine.begin() as conn:
                result = conn.execute(users.insert().values(name=data['name'].strip(), email=data['email'].strip().lower(),
                    password_hash=generate_password_hash(data['password']), role='agent', created_at=now()))
                row = conn.execute(select(users).where(users.c.id == result.inserted_primary_key[0])).mappings().one()
                return jsonify(public(row)), 201
        except IntegrityError:
            return jsonify(error='Email already registered'), 409

    @app.get('/api/tickets')
    @auth
    def list_tickets():
        with engine.connect() as conn:
            return jsonify(enrich(conn, conn.execute(select(tickets).where(scope()).order_by(tickets.c.updated_at.desc(), tickets.c.id.desc())).mappings().all()))

    @app.post('/api/tickets')
    @auth
    def create_ticket():
        data = body()
        if set(data)-{'title','description','priority','category'} or not string(data.get('title'),160) or not string(data.get('description'),8000):
            return jsonify(error='Provide a title (1–160 characters) and description (1–8000 characters)'), 400
        priority, category = data.get('priority','medium'), data.get('category','General')
        if priority not in PRIORITIES or category not in CATEGORIES:
            return jsonify(error='Choose a valid priority and category'), 400
        timestamp = now()
        due = (datetime.now(timezone.utc)+timedelta(hours=SLA_HOURS[priority])).isoformat()
        with engine.begin() as conn:
            result = conn.execute(tickets.insert().values(title=data['title'].strip(), description=data['description'].strip(),
                status='open', priority=priority, category=category, requester_id=g.user['id'], created_at=timestamp, updated_at=timestamp, due_at=due))
            ticket_id = result.inserted_primary_key[0]
            audit(conn,ticket_id,'created this ticket')
            return jsonify(enrich(conn,[find(conn,ticket_id)])[0]), 201

    @app.get('/api/tickets/<int:ticket_id>')
    @auth
    def get_ticket(ticket_id):
        with engine.connect() as conn:
            row = find(conn,ticket_id)
            if not row:
                return jsonify(error='Ticket not found'), 404
            result = enrich(conn,[row])[0]
            result['comments'] = [dict(item) for item in conn.execute(select(comments,users.c.name.label('author'),users.c.role.label('author_role')).join(users,comments.c.author_id==users.c.id).where(comments.c.ticket_id==ticket_id).order_by(comments.c.id)).mappings()]
            result['activity'] = [dict(item) for item in conn.execute(select(activities,users.c.name.label('actor')).join(users,activities.c.actor_id==users.c.id).where(activities.c.ticket_id==ticket_id).order_by(activities.c.id.desc())).mappings()]
            return jsonify(result)

    @app.patch('/api/tickets/<int:ticket_id>')
    @auth
    def update_ticket(ticket_id):
        data = body()
        allowed = {'title','description','priority','category'} | ({'status','assignee_id'} if g.user['role'] in ('admin','agent') else set())
        if not data or set(data)-allowed:
            return jsonify(error='You cannot update those ticket fields'), 403
        if ('title' in data and not string(data['title'],160)) or ('description' in data and not string(data['description'],8000)):
            return jsonify(error='Title or description is invalid'), 400
        for field, choices in [('status',STATUSES),('priority',PRIORITIES),('category',CATEGORIES)]:
            if field in data and data[field] not in choices:
                return jsonify(error=f'Invalid {field}'), 400
        with engine.begin() as conn:
            row = find(conn,ticket_id)
            if not row:
                return jsonify(error='Ticket not found'), 404
            if 'assignee_id' in data and data['assignee_id'] is not None:
                if type(data['assignee_id']) is not int or not conn.execute(select(users.c.id).where(users.c.id==data['assignee_id'],users.c.role.in_(['admin','agent']))).first():
                    return jsonify(error='Assign tickets to a support team member'), 400
            updates = {key:value.strip() if isinstance(value,str) else value for key,value in data.items()}
            if 'status' in updates and updates['status'] != row['status']:
                updates['resolved_at'] = now() if updates['status']=='resolved' else None
            if 'priority' in updates and updates['priority'] != row['priority']:
                updates['due_at'] = (datetime.fromisoformat(row['created_at'])+timedelta(hours=SLA_HOURS[updates['priority']])).isoformat()
            changed = [field.replace('_id','').replace('_',' ') for field in data if data[field]!=row[field]]
            updates['updated_at'] = now()
            conn.execute(tickets.update().where(tickets.c.id==ticket_id).values(**updates))
            if changed:
                audit(conn,ticket_id,'updated '+', '.join(changed))
            return jsonify(enrich(conn,[find(conn,ticket_id)])[0])

    @app.delete('/api/tickets/<int:ticket_id>')
    @auth
    def delete_ticket(ticket_id):
        with engine.begin() as conn:
            row = find(conn,ticket_id)
            if not row:
                return jsonify(error='Ticket not found'), 404
            if row['requester_id']!=g.user['id'] and g.user['role']!='admin':
                return jsonify(error='Only the requester or administrator can delete a ticket'), 403
            conn.execute(tickets.delete().where(tickets.c.id==ticket_id))
        return '', 204

    @app.post('/api/tickets/<int:ticket_id>/comments')
    @auth
    def add_comment(ticket_id):
        data = body()
        if not string(data.get('body'),4000):
            return jsonify(error='Write a comment of 1–4000 characters'), 400
        with engine.begin() as conn:
            if not find(conn,ticket_id):
                return jsonify(error='Ticket not found'), 404
            conn.execute(comments.insert().values(ticket_id=ticket_id,author_id=g.user['id'],body=data['body'].strip(),created_at=now()))
            conn.execute(tickets.update().where(tickets.c.id==ticket_id).values(updated_at=now()))
            audit(conn,ticket_id,'added a comment')
        return jsonify(message='Comment added'), 201

    @app.get('/api/dashboard')
    @auth
    def dashboard():
        with engine.connect() as conn:
            rows = enrich(conn,conn.execute(select(tickets).where(scope())).mappings().all())
            recent = conn.execute(select(activities,tickets.c.title.label('ticket_title'),users.c.name.label('actor')).join(tickets,activities.c.ticket_id==tickets.c.id).join(users,activities.c.actor_id==users.c.id).where(scope()).order_by(activities.c.id.desc()).limit(8)).mappings().all()
        today = datetime.now(timezone.utc).date()
        weekly = [{'date':(today-timedelta(days=i)).isoformat()} for i in reversed(range(7))]
        for day in weekly:
            day['created'] = sum(row['created_at'][:10]==day['date'] for row in rows)
            day['resolved'] = sum(bool(row['resolved_at']) and row['resolved_at'][:10]==day['date'] for row in rows)
        return jsonify(total=len(rows), active=sum(row['status']!='resolved' for row in rows),
            unassigned=sum(row['assignee_id'] is None and row['status']!='resolved' for row in rows),
            overdue=sum(row['overdue'] for row in rows),resolved_week=sum(day['resolved'] for day in weekly),
            statuses={s:sum(row['status']==s for row in rows) for s in STATUSES},
            priorities={p:sum(row['priority']==p and row['status']!='resolved' for row in rows) for p in PRIORITIES},
            weekly=weekly,activity=[dict(row,key=f'HD-{1000+row["ticket_id"]}') for row in recent])
    return app
