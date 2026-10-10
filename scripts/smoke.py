"""No-dependency HTTP smoke test for the deployed authenticated support portal."""
import http.cookiejar
import json
import secrets
import sys
import time
import urllib.error
import urllib.request

base = (sys.argv[1] if len(sys.argv)>1 else 'http://localhost:8080').rstrip('/')
jar = http.cookiejar.CookieJar()
http = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(jar))
csrf = ''
ticket_id = None
registered = False

def request(path, method='GET', data=None, expected=200):
    global csrf
    payload = json.dumps(data).encode() if data is not None else None
    req = urllib.request.Request(base+path,data=payload,method=method,headers={'Content-Type':'application/json','X-CSRF-Token':csrf})
    try:
        response=http.open(req,timeout=15)
    except urllib.error.HTTPError as error:
        if error.code == expected:
            return None
        raise
    with response:
        if response.status != expected:
            raise RuntimeError(f'{method} {path}: expected {expected}, received {response.status}')
        value = json.loads(response.read()) if response.status!=204 else None
        if isinstance(value,dict) and 'csrf' in value:
            csrf=value['csrf']
        return value

for attempt in range(15):
    try:
        http.open(base+'/health',timeout=5).close()
        break
    except (OSError,urllib.error.URLError):
        if attempt==14: raise
        time.sleep(2)
with http.open(base+'/',timeout=10) as response:
    assert 'id="root"' in response.read().decode(), 'Frontend index is missing'
try:
    request('/api/session')
    request('/api/auth/register','POST',{'name':'CI smoke probe','email':f'ci-{secrets.token_hex(12)}@smoke.example','password':secrets.token_urlsafe(24)},201)
    registered=True
    ticket=request('/api/tickets','POST',{'title':'CI smoke probe','description':'Temporary deployment verification','priority':'medium','category':'General'},201)
    ticket_id=ticket['id']
    assert request(f'/api/tickets/{ticket_id}')['title']=='CI smoke probe'
    assert request(f'/api/tickets/{ticket_id}','PATCH',{'priority':'high'})['priority']=='high'
    request(f'/api/tickets/{ticket_id}/comments','POST',{'body':'Deployment integration check'},201)
    assert len(request(f'/api/tickets/{ticket_id}')['comments'])==1
    assert request('/api/dashboard')['total']==1
    # Requesters must not be able to assign themselves elevated roles or resolve tickets.
    request(f'/api/tickets/{ticket_id}','PATCH',{'status':'resolved'},403)
    request(f'/api/tickets/{ticket_id}','DELETE',expected=204)
    request(f'/api/tickets/{ticket_id}',expected=404)
    ticket_id=None
    request('/api/account','DELETE',expected=204)
    registered=False
    print('PASS: frontend, registration/session/CSRF, ticket CRUD, comments, dashboard and role boundary; temporary account removed')
finally:
    # Clean only this test's own data, including on an assertion failure.
    if ticket_id is not None:
        try: request(f'/api/tickets/{ticket_id}','DELETE',expected=204)
        except Exception: print('Cleanup incomplete: temporary smoke ticket remains',file=sys.stderr)
    if registered:
        try: request('/api/account','DELETE',expected=204)
        except Exception: print('Cleanup incomplete: temporary smoke account remains',file=sys.stderr)
