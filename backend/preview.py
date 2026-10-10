"""Launch an explicit loopback-only SQLite preview with a sample admin workspace."""
import secrets
from pathlib import Path
from flask import send_from_directory
from portal import create_app
from seed import seed_demo

root = Path(__file__).resolve().parents[1]
state = root / '.preview'
state.mkdir(exist_ok=True)
key_file = state/'secret.key'
if not key_file.exists():
    key_file.write_text(secrets.token_hex(32))
    key_file.chmod(0o600)
app = create_app('sqlite:///'+(state/'support.db').as_posix(),secret_key=key_file.read_text().strip())
app.config['DEMO_USER_ID'] = seed_demo(app)
assets=root/'frontend'/'dist'

@app.get('/')
def index():
    return send_from_directory(assets,'index.html')

@app.get('/assets/<path:filename>')
def asset(filename):
    return send_from_directory(assets/'assets',filename)

if __name__=='__main__':
    if not (assets/'index.html').exists():
        raise SystemExit('Build the frontend first: cd frontend && npm ci && npm run build')
    app.run(host='127.0.0.1',port=8081,debug=False,use_reloader=False)
