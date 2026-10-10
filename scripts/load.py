"""Bounded authenticated traffic; the temporary requester is deleted afterward."""
import http.cookiejar
import json
import secrets
import sys
import time
import urllib.request

base=(sys.argv[1] if len(sys.argv)>1 else 'http://localhost:8080').rstrip('/')
count=int(sys.argv[2]) if len(sys.argv)>2 else 300
if not 1<=count<=10000:
    raise SystemExit('Choose a request count between 1 and 10000')
http=urllib.request.build_opener(urllib.request.HTTPCookieProcessor(http.cookiejar.CookieJar()))
csrf=''
def request(path,method='GET',data=None):
    global csrf
    req=urllib.request.Request(base+path,method=method,data=json.dumps(data).encode() if data is not None else None,headers={'Content-Type':'application/json','X-CSRF-Token':csrf})
    with http.open(req,timeout=10) as response:
        value=json.loads(response.read()) if response.status!=204 else None
        if isinstance(value,dict) and 'csrf' in value: csrf=value['csrf']
        return value
request('/api/session')
request('/api/auth/register','POST',{'name':'Load probe','email':f'load-{secrets.token_hex(12)}@smoke.example','password':secrets.token_urlsafe(24)})
try:
    for i in range(count):
        request('/api/dashboard' if i%3==0 else '/api/tickets')
        time.sleep(.2)
    print(f'Completed {count} authenticated requests')
finally:
    request('/api/account','DELETE')
