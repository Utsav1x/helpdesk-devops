"""Explicit sample-data seeding for the local preview, never automatic in production."""
import secrets
from datetime import datetime, timedelta, timezone
from sqlalchemy import select
from werkzeug.security import generate_password_hash
from portal import SLA_HOURS

def seed_demo(app):
    db = app.extensions['db']
    users, tickets, comments, activities = (app.extensions['tables'][key] for key in ('users','tickets','comments','activities'))
    clock = datetime.now(timezone.utc)
    with db.begin() as conn:
        existing = conn.execute(select(users.c.id).where(users.c.email=='maya@preview.example')).scalar_one_or_none()
        if existing:
            return existing
        people = [('Maya Chen','admin'),('Alex Morgan','agent'),('Jordan Lee','agent'),('Sam Rivera','requester'),('Emma Wilson','requester'),('Noah Patel','requester'),('Olivia Taylor','requester')]
        ids=[]
        for name,role in people:
            email = 'maya@preview.example' if name=='Maya Chen' else name.lower().replace(' ','.')+'@preview.example'
            result=conn.execute(users.insert().values(name=name,email=email,password_hash=generate_password_hash(secrets.token_urlsafe(32)),role=role,created_at=clock.isoformat()))
            ids.append(result.inserted_primary_key[0])
        samples=[
            ('Unable to access the team workspace','Account access','urgent','open',None,3,0),
            ('VPN keeps disconnecting during calls','Network','high','in_progress',1,4,1),
            ('Update billing contact for our account','Billing','medium','waiting',2,5,2),
            ('Laptop screen flickers when connected to dock','Hardware','high','open',None,6,1),
            ('Request access to the design software','Software','low','in_progress',1,3,2),
            ('Reset two-factor authentication','Account access','medium','resolved',0,4,3),
            ('Shared printer is showing offline','Hardware','medium','resolved',2,5,4),
            ('New starter needs a workspace account','Account access','low','open',1,6,0),
            ('Exported reports have missing columns','Software','high','waiting',0,3,3),
            ('Office Wi-Fi is slow on the second floor','Network','medium','resolved',1,4,5),
            ('Invoice has an incorrect company address','Billing','low','resolved',2,5,6),
            ('Email notifications are not arriving','Software','medium','in_progress',0,6,1),
            ('Help setting up a second monitor','Hardware','low','resolved',1,3,4),
            ('Permission error opening shared drive','Account access','high','open',None,4,0),
        ]
        for i,(title,category,priority,status,agent,requester,days) in enumerate(samples):
            created=clock-timedelta(days=days,hours=(i%4)+1)
            resolved=(created+timedelta(hours=3)).isoformat() if status=='resolved' else None
            result=conn.execute(tickets.insert().values(title=title,description=f'{title}.\n\nThis is affecting my daily work. I have already tried restarting and checking the available settings, but the issue persists. Could the support team take a look?\n\nThis is a sample request for exploring the support portal.',status=status,priority=priority,category=category,requester_id=ids[requester],assignee_id=ids[agent] if agent is not None else None,created_at=created.isoformat(),updated_at=(created+timedelta(minutes=30)).isoformat(),due_at=(created+timedelta(hours=SLA_HOURS[priority])).isoformat(),resolved_at=resolved))
            ticket_id=result.inserted_primary_key[0]
            conn.execute(activities.insert().values(ticket_id=ticket_id,actor_id=ids[requester],message='created this ticket',created_at=created.isoformat()))
            if agent is not None:
                conn.execute(comments.insert().values(ticket_id=ticket_id,author_id=ids[agent],body='Thanks for sharing the details. I have picked this up and will keep you posted here.' if status!='resolved' else 'This has now been resolved. Please let us know in a reply if you need any further help.',created_at=(created+timedelta(minutes=30)).isoformat()))
                conn.execute(activities.insert().values(ticket_id=ticket_id,actor_id=ids[agent],message='added a comment',created_at=(created+timedelta(minutes=30)).isoformat()))
        return ids[0]
