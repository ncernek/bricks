"""Module to test notification sending"""
import datetime as dt
import pytz
from tests.config_test import BaseTestCase
from app.models import AppUser, Exchange, Task, Team, TeamMember, Notification, Point
from app.get_router import get_router
from app.constants import US_TIMEZONES, Statuses, RouterNames
from app import notify

class TestNotifications(BaseTestCase):
    mitch_tz = US_TIMEZONES['b']
    local_now = dt.datetime.now(tz=pytz.timezone(mitch_tz))
    number = '+13124505311'

    def setUp(self):
        super().setUp()
        # add a user
        self.mitch = AppUser(
            phone_number=self.number, 
            username='Mitch',
            timezone=self.mitch_tz)
        self.db.session.add(self.mitch)

        # add exchange
        self.exchange = Exchange(
            router = RouterNames.DID_YOU_DO_IT,
            outbound = 'Did you do it?',
            user = self.mitch)
        self.db.session.add(self.exchange)

        # add a notif
        self.did_you_do_it_notif = Notification(
            router = RouterNames.DID_YOU_DO_IT,
            day_of_week = 'daily',
            hour = self.local_now.hour,
            minute = self.local_now.minute,
            active = True,
            user = self.mitch)
        self.db.session.add(self.did_you_do_it_notif)

        self.morning_conf_notif = Notification(
            router = RouterNames.MORNING_CONFIRMATION,
            day_of_week = 'daily',
            hour = self.local_now.hour,
            minute = self.local_now.minute,
            active = True,
            user = self.mitch)
        self.db.session.add(self.morning_conf_notif)

        self.week_reflection_notif = Notification(
            router = RouterNames.WEEK_REFLECTION,
            day_of_week = 'daily',
            hour = self.local_now.hour,
            minute = self.local_now.minute,
            active = True,
            user = self.mitch)
        self.db.session.add(self.week_reflection_notif)        

        # add task
        self.task = Task(
            description='Win today',
            due_date = dt.datetime.now()+ dt.timedelta(minutes=1),
            active = True,
            exchange = self.exchange,
            user = self.mitch)
        self.db.session.add(self.task)

    def test_notify(self):
        '''test that notifications send whose time corresponds with now'''
        response = self.client.get('/notify')

        print(response.data)

    def test_no_notifications(self):
        '''test that no notifications are sent if user tz is None'''
        self.mitch.timezone = None
        message = notify.main()
        assert message.response[0] == b'[]' 
