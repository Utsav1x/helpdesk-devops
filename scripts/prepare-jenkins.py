"""Create private first-run inputs from the authorized GitHub CLI account."""
import argparse
import json
import os
from pathlib import Path
import re
import secrets
import subprocess

parser=argparse.ArgumentParser()
parser.add_argument('--repository', required=True, help='Existing GitHub owner/repository')
parser.add_argument('--gh-config', help='Optional GitHub CLI config directory for this setup')
args=parser.parse_args()
if not re.fullmatch(r'[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+',args.repository):
    raise SystemExit('Use an owner/repository name, not a URL.')
root=Path(__file__).resolve().parents[1]
environment=os.environ.copy()
if args.gh_config:
    environment['GH_CONFIG_DIR']=str(Path(args.gh_config).resolve())
def gh(*arguments):
    result=subprocess.run(['gh',*arguments],env=environment,capture_output=True,text=True)
    if result.returncode:
        raise SystemExit('GitHub authorization or repository access failed. Run gh auth login and try again.')
    return result.stdout.strip()
account=json.loads(gh('api','user'))['login']
repository=json.loads(gh('api',f'repos/{args.repository}'))
if not repository.get('permissions',{}).get('admin'):
    raise SystemExit('Use a repository you administer for this lab.')
token=gh('auth','token','--hostname','github.com')
directory=root/'.bootstrap'
directory.mkdir(exist_ok=True)
directory.chmod(0o700)
def write(name,value):
    path=directory/name
    path.write_text(value,encoding='utf-8')
    path.chmod(0o600)
write('github-user.txt',account)
write('github-token.txt',token)
write('repository.txt',args.repository)
if not (directory/'jenkins-admin-password.txt').exists():
    write('jenkins-admin-password.txt',secrets.token_urlsafe(32))
for name in ('production','staging'):
    source=root/f'.env.{name}'
    if not source.exists():
        raise SystemExit('Run python scripts/init-env.py first.')
    write(f'{name}.env',source.read_text(encoding='utf-8'))
print('Prepared private Jenkins inputs. No credential values printed.')
print('Jenkins username: helpdesk-admin')
print('Password is in .bootstrap/jenkins-admin-password.txt; do not commit or share it.')
