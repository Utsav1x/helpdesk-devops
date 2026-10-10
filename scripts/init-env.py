"""Generate ignored local environment files without printing their secrets."""
from pathlib import Path
import secrets

root = Path(__file__).resolve().parents[1]
template = (root / '.env.example').read_text()
for name, front, back in [('production', 8080, 8000), ('staging', 8081, 8001)]:
    path = root / f'.env.{name}'
    if path.exists():
        # Upgrade old files without changing existing passwords or signing keys.
        current = path.read_text()
        if not any(line.startswith('SECRET_KEY=') and line.split('=',1)[1].strip() for line in current.splitlines()):
            lines = [line for line in current.splitlines() if not line.startswith('SECRET_KEY=')]
            path.write_text('\n'.join(lines) + '\n# Session-signing key for the support portal.\nSECRET_KEY=' + secrets.token_hex(32) + '\n', encoding='utf-8')
            print(f'Added missing session key to {path.name}; existing credentials preserved.')
        else:
            print(f'Kept existing {path.name}')
        continue
    values = {'APP_ENV': name, 'FRONTEND_PORT': str(front), 'BACKEND_PORT': str(back),
              'POSTGRES_PASSWORD': secrets.token_hex(24), 'GRAFANA_ADMIN_PASSWORD': secrets.token_hex(24), 'SECRET_KEY': secrets.token_hex(32)}
    lines = []
    for line in template.splitlines():
        key = line.split('=', 1)[0]
        lines.append(f'{key}={values[key]}' if key in values else line)
    with path.open('x', encoding='utf-8', newline='\n') as file:
        file.write('\n'.join(lines) + '\n')
    path.chmod(0o600)
    print(f'Created {path.name}; keep it private and out of Git.')
