import datetime as dt
from sqlalchemy import func
from app import scheduler, db
from app.models import AppUser, Notification, Point
from app.send_notifications import add_notif_to_scheduler
from app.routers import nodes
from config import Config # TODO(Nico) access the config that has been initialized on the app 
    

def schedule_reminders(user, **kwargs):
    '''Create one morning and one evening reminder. Add reminders to scheduler and to db'''

    # set morning reminder
    if len(Notification.query.filter_by(user_id=user['id'], tag='choose_brick').all()) == 0:

        outbound = nodes[nodes.router_id == 'choose_brick'].iloc[0]

        notif = Notification(tag=outbound.router_id,
            body=outbound.outbound,
            trigger_type='cron',
            day_of_week='mon-fri',
            hour=8,
            minute=0,
            jitter=30,
            end_date=dt.datetime(2018,11,30),
            timezone=user.get('timezone', 'America/Los_Angeles'),
            user_id=user['id'])
        
        # TODO(Nico) it could be problematic to schedule this before committing to db
        add_notif_to_scheduler(scheduler, notif, user, Config)
        db.session.add(notif)

    # set evening reminder
    if len(Notification.query.filter_by(user_id=user['id'], tag='evening_checkin').all()) == 0:

        outbound = nodes[nodes.router_id == 'evening_checkin'].iloc[0]

        notif = Notification(tag=outbound.router_id,
            body=outbound.outbound,
            trigger_type='cron',
            day_of_week='mon-fri',
            hour=21,
            minute=0,
            jitter=30,
            end_date=dt.datetime(2018,11,30),
            timezone=user.get('timezone', 'America/Los_Angeles'),
            user_id=user['id'])
        
        # TODO(Nico) it could be problematic to schedule this before committing to db
        add_notif_to_scheduler(scheduler, notif, user, Config)
        db.session.add(notif)

    db.session.commit()


def update_timezone(inbound, user, **kwargs):
    tz = Config.US_TIMEZONES.get(inbound, None)
    if tz is not None:        
        user_obj = db.session.query(AppUser).filter_by(id=user['id']).one()
        user_obj.timezone = tz
        user['timezone'] = tz

        # update all notifications for that user in the db
        # TODO(Nico) update notifications in the scheduler
        notifs = db.session.query(Notification).filter_by(user_id=user['id']).all()
        for notif in notifs:
            notif.timezone = tz
            
        db.session.commit()

    else:
        raise ValueError('INVALID TIMEZONE CHOICE')

    return tz


def update_username(inbound, user, **kwargs):
    user_obj = db.session.query(AppUser).filter_by(id=user['id']).one()
    user_obj.username = inbound
    user['username'] = inbound

    db.session.commit()


def add_point(user, **kwargs):
    point = Point(value=1, user_id=user['id'])
    db.session.add(point)
    db.session.commit()


def query_points(user, **kwargs):
    points = db.session.query(func.sum(Point.value).label('points')).filter(Point.user_id == user['id']).one()[0]

    if points is None:
        return 0
    else:
        return points


ROUTER_ACTIONS = dict(
    schedule_reminders = schedule_reminders,
    update_timezone = update_timezone,
    update_username = update_username,
    add_point = add_point,
    query_points = query_points)