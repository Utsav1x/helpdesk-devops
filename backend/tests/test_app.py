import secrets
import pytest
from sqlalchemy import select
from sqlalchemy.exc import OperationalError
from werkzeug.security import generate_password_hash
from app import create_app
from portal import now

@pytest.fixture
def app(tmp_path):
    app=create_app(f'sqlite:///{tmp_path/"test.db"}',secret_key=secrets.token_hex(32))
    app.config['TESTING']=True
    yield app
    app.extensions['db'].dispose()

@pytest.fixture
def client(app):
    return app.test_client()

def call(client,method,path,data=None):
    csrf=client.get('/api/session').json['csrf']
    return client.open(path,method=method,json=data,headers={'X-CSRF-Token':csrf})

def register(client,email='requester@example.test'):
    return call(client,'POST','/api/auth/register',{'name':'Test Requester','email':email,'password':secrets.token_urlsafe(16)})

def staff(app,role='agent'):
    password=secrets.token_urlsafe(16)
    users=app.extensions['tables']['users']
    with app.extensions['db'].begin() as conn:
        conn.execute(users.insert().values(name='Support Agent',email=f'{role}@example.test',password_hash=generate_password_hash(password),role=role,created_at=now()))
    client=app.test_client()
    response=call(client,'POST','/api/auth/login',{'email':f'{role}@example.test','password':password})
    assert response.status_code==200
    return client,response.json['user']['id']

def ticket(client):
    response=call(client,'POST','/api/tickets',{'title':'Cannot sign in','description':'The workspace shows a login error.','priority':'high','category':'Account access'})
    assert response.status_code==201
    return response.json

def test_health(client):
    assert client.get('/health').json=={'status':'ok'}

def test_auth_required(client):
    assert client.get('/api/tickets').status_code==401
    assert client.get('/api/dashboard').status_code==401

def test_csrf_required(client):
    assert client.post('/api/auth/register',json={}).status_code==403

def test_registration_hides_hash(client):
    response=register(client)
    assert response.status_code==201
    assert response.json['user']['role']=='requester'
    assert 'password_hash' not in response.text
    assert client.get('/api/session').json['user']['name']=='Test Requester'

def test_registration_cannot_elevate_role(client):
    assert call(client,'POST','/api/auth/register',{'name':'X','email':'x@test.test','password':secrets.token_hex(12),'role':'admin'}).status_code==400

def test_duplicate_email(client):
    register(client)
    assert register(client).status_code==409

def test_bad_login(client):
    register(client)
    assert call(client,'POST','/api/auth/login',{'email':'requester@example.test','password':'incorrectpassword'}).status_code==401

def test_logout_invalidates_session(client):
    register(client)
    assert call(client,'POST','/api/auth/logout').status_code==200
    assert client.get('/api/tickets').status_code==401

def test_demo_disabled_by_default(client):
    assert client.get('/api/session').json['demo'] is False
    assert call(client,'POST','/api/auth/demo').status_code==404

def test_create_read_update_delete(client):
    register(client)
    t=ticket(client)
    assert t['status']=='open' and t['key'].startswith('HD-')
    assert client.get(f'/api/tickets/{t["id"]}').json['title']=='Cannot sign in'
    assert call(client,'PATCH',f'/api/tickets/{t["id"]}',{'title':'New title'}).json['title']=='New title'
    assert call(client,'DELETE',f'/api/tickets/{t["id"]}').status_code==204
    assert client.get(f'/api/tickets/{t["id"]}').status_code==404

@pytest.mark.parametrize('data',[{},[],{'title':' ','description':'x'},{'title':'x','description':''},{'title':'x'*161,'description':'x'},{'title':'x','description':'x','priority':'critical'},{'title':'x','description':'x','category':'Unknown'}])
def test_invalid_ticket(client,data):
    register(client)
    assert call(client,'POST','/api/tickets',data).status_code==400

def test_requester_isolation(app,client):
    register(client)
    t=ticket(client)
    other=app.test_client()
    register(other,'other@example.test')
    assert other.get('/api/tickets').json==[]
    assert other.get(f'/api/tickets/{t["id"]}').status_code==404
    assert call(other,'PATCH',f'/api/tickets/{t["id"]}',{'title':'Hacked'}).status_code==404
    assert call(other,'POST',f'/api/tickets/{t["id"]}/comments',{'body':'Hacked'}).status_code==404
    assert call(other,'DELETE',f'/api/tickets/{t["id"]}').status_code==404
    assert other.get('/api/dashboard').json['total']==0

def test_requester_cannot_assign_or_resolve(client):
    register(client)
    t=ticket(client)
    assert call(client,'PATCH',f'/api/tickets/{t["id"]}',{'status':'resolved'}).status_code==403
    assert call(client,'PATCH',f'/api/tickets/{t["id"]}',{'assignee_id':1}).status_code==403

def test_agent_assignment_and_resolution(app,client):
    register(client)
    t=ticket(client)
    agent,user_id=staff(app)
    response=call(agent,'PATCH',f'/api/tickets/{t["id"]}',{'assignee_id':user_id,'status':'resolved'})
    assert response.status_code==200
    assert response.json['assignee_id']==user_id and response.json['resolved_at']
    assert response.json['overdue'] is False
    assert call(agent,'PATCH',f'/api/tickets/{t["id"]}',{'status':'open'}).json['resolved_at'] is None

def test_invalid_assignment(app,client):
    requester=register(client).json['user']['id']
    t=ticket(client)
    agent,_=staff(app)
    for assignee in [requester,999,True,'1']:
        assert call(agent,'PATCH',f'/api/tickets/{t["id"]}',{'assignee_id':assignee}).status_code==400

def test_agent_cannot_delete_others_ticket(app,client):
    register(client)
    t=ticket(client)
    agent,_=staff(app)
    assert call(agent,'DELETE',f'/api/tickets/{t["id"]}').status_code==403

def test_comments_and_activity(client):
    register(client)
    t=ticket(client)
    assert call(client,'POST',f'/api/tickets/{t["id"]}/comments',{'body':'More details'}).status_code==201
    detail=client.get(f'/api/tickets/{t["id"]}').json
    assert detail['comments'][0]['body']=='More details'
    assert detail['activity'][0]['message']=='added a comment'

def test_delete_cascades_comments(client,app):
    register(client)
    t=ticket(client)
    call(client,'POST',f'/api/tickets/{t["id"]}/comments',{'body':'Details'})
    call(client,'DELETE',f'/api/tickets/{t["id"]}')
    with app.extensions['db'].connect() as conn:
        assert conn.execute(select(app.extensions['tables']['comments'])).all()==[]

def test_dashboard_counts(app,client):
    register(client)
    t=ticket(client)
    d=client.get('/api/dashboard').json
    assert d['total']==1 and d['active']==1 and d['unassigned']==1 and len(d['weekly'])==7
    agent,_=staff(app)
    call(agent,'PATCH',f'/api/tickets/{t["id"]}',{'status':'resolved'})
    assert client.get('/api/dashboard').json['resolved_week']==1

def test_admin_adds_agent(app):
    admin,_=staff(app,'admin')
    data={'name':'New Agent','email':'new@example.test','password':secrets.token_hex(12)}
    assert call(admin,'POST','/api/team',data).status_code==201
    assert call(admin,'POST','/api/team',data).status_code==409
    assert len(admin.get('/api/team').json)==2

def test_requester_cannot_add_agent(client):
    register(client)
    assert call(client,'POST','/api/team',{}).status_code==403

def test_account_cleanup(client):
    register(client)
    t=ticket(client)
    assert call(client,'DELETE','/api/account').status_code==409
    call(client,'DELETE',f'/api/tickets/{t["id"]}')
    assert call(client,'DELETE','/api/account').status_code==204
    assert client.get('/api/session').json['user'] is None

def test_metrics(client):
    client.get('/api/tickets')
    metrics=client.get('/metrics').text
    assert 'http_requests_total{method="GET",route="/api/tickets",status="401"} 1.0' in metrics
    assert 'http_request_duration_seconds_bucket' in metrics

def test_database_failure(client,app,monkeypatch):
    def fail():
        raise OperationalError('SELECT 1',{},Exception('offline'))
    monkeypatch.setattr(app.extensions['db'],'connect',fail)
    assert client.get('/health').status_code==503

def test_security_headers(client):
    response=client.get('/api/session')
    assert response.headers['Cache-Control']=='no-store'
    assert 'HttpOnly' in response.headers['Set-Cookie'] and 'SameSite=Lax' in response.headers['Set-Cookie']

def test_missing_secret_rejected(monkeypatch,tmp_path):
    monkeypatch.delenv('SECRET_KEY',raising=False)
    with pytest.raises(RuntimeError):
        create_app(f'sqlite:///{tmp_path/"no-key.db"}')
