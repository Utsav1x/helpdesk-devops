"""Create the initial administrator interactively; passwords never enter shell history."""
import getpass
from sqlalchemy import select
from werkzeug.security import generate_password_hash
from portal import create_app, now

if __name__ == '__main__':
    app = create_app()
    users = app.extensions['tables']['users']
    name = input('Administrator name: ').strip()
    email = input('Administrator email: ').strip().lower()
    password = getpass.getpass('Password (10–128 characters): ')
    confirmation = getpass.getpass('Confirm password: ')
    if not 1 <= len(name) <= 80 or '@' not in email or len(email) > 200 or not 10 <= len(password) <= 128 or password != confirmation:
        raise SystemExit('Invalid name/email/password or passwords did not match.')
    with app.extensions['db'].begin() as conn:
        if conn.execute(select(users.c.id).where(users.c.email == email)).first():
            raise SystemExit('Account already exists; no changes made.')
        conn.execute(users.insert().values(name=name, email=email, password_hash=generate_password_hash(password), role='admin', created_at=now()))
    print('Administrator created. Sign in through the website, then add agents under Team.')
