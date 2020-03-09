from __future__ import absolute_import, unicode_literals

import datetime
import pytz

from celery import task
from django.db import connection

from ccalendar.models import Google
from ccalendar.utils import refresh_token_from_google
from meeting.models import Host, Details, Status
from organization.models import Organization
from notifications.models import Notification


'''
Run every 20 minutes. Refreshes all the access tokens of users who are logged in to the system.
'''
@task
def refresh_token_google():
    redirect_uri = 'http://localhost:8000/api/calendar'
    connection.set_schema_to_public()

    all_schemas = Organization.objects.all().exclude(schema_name='public')

    for schema in all_schemas:
        schema_name = schema.schema_name
        connection.set_schema(schema_name=schema_name)

        user_tokens = Google.objects.all()

        for tokens in user_tokens:
            refresh_token = tokens.refresh
            token = refresh_token_from_google(refresh_token, redirect_uri)
            tokens.access = token['access_token']
            tokens.save()


'''
Run every midnight UTC. If the subscription expires, 
change active status of all users and the organization except the admin to inactive.

Remove meeting drafts too.
'''
@task
def check_company_subscription():
    all_schemas = Organization.objects.all().exclude(schema_name='public')
    now = datetime.datetime.now(pytz.UTC)
    datetoday = now.date()

    for schema in all_schemas:
        if schema.is_active and schema.subscription_expiry < datetoday:
            schema.is_active = False
            schema.save()


'''
Send reminders to participants/host that the meeting is starting soon.
If the participant has not accepted/declined till the start of the meeting,
the participant will decline the meeting. The reason for declining will be
failed to respond in time.

Planning to run every minute.
Rewrite this code.
'''

@task
def reminders_of_meeting():
    all_schemas = Organization.objects.all().exclude(schema_name='public')
    
    datetimetoday = datetime.datetime.now(pytz.UTC)
    datetimetoday = datetimetoday.replace(microsecond=0)

    datetimetenmin = datetimetoday + datetime.timedelta(minutes=10)
    datetimefivemin = datetimetoday + datetime.timedelta(minutes=5)

    for schema in all_schemas:
        connection.set_schema(schema_name=schema.schema_name)

        all_meetings = Details.objects.filter(
            meeting_date=datetimetoday.date())

        for meeting in all_meetings:
            host_meeting = Host.objects.get(uid=meeting.meeting.uid)
            participants = Status.objects.filter(meeting_host=meeting.meeting)

            if datetimetenmin.time() == meeting.start_time:
                title = 'Reminder for meeting'
                message = meeting.meeting.title + \
                    ' starts soon. Please respond to the meeting if you have not done so already.'
                notification_type = 'meeting'

                notification = Notification(
                    title=title, message=message, notification_type=notification_type, meeting=meeting, user=meeting.meeting.host)
                notification.save()

                for participant in participants:
                    if participant.participant_status != 'PE':
                        continue

                    notification = Notification(
                        title=title, message=message, notification_type=notification_type, meeting=meeting, user=participant.participant)
                    notification.save()

            if datetimefivemin.time() == meeting.start_time:
                title = 'Reminder for meeting'
                message = 'Meeting ' + meeting.meeting.title + \
                    ' starts in 5 minutes. Since you have not responded to the invitation. The app has declined the invitation for you.'
                notification_type = 'meeting'

                for participant in participants:
                    if not participant.participant_status in ['AC', 'DE', 'PO']:
                        participant.participant_status = 'DE'
                        participant.participant_message = 'Failed to respond in time. (System Generated)'
                        participant.save()

                        notification = Notification(
                            title=title, message=message, notification_type=notification_type, meeting=meeting, user=participant.participant)
                        notification.save()

            all_response = True
            for participant in participants:
                if participant.participant_status in ['PE', 'PO']:
                    all_response = False


            if all_response and host_meeting.meeting_status in ['IN']:
                host_meeting.meeting_status = 'FI'
                host_meeting.save()

'''
Check the meeting status every minute. If the meeting time has passed change the
meeting status to completed. If the meeting status is canceled, delete the meeting
after 72 hours.
'''
@task
def check_meeting_status():
    all_schemas = Organization.objects.all().exclude(schema_name='public')
    datetimetoday = datetime.datetime.now(pytz.UTC)

    for schema in all_schemas:
        connection.set_schema(schema_name=schema.schema_name)

        all_meetings = Details.objects.filter(
            meeting_date=datetimetoday.date())

        for meeting in all_meetings:
            meeting_host = Host.objects.get(uid=meeting.meeting.uid)

            if meeting_host.meeting_status in ['IN', 'FI', 'ON']:
                if meeting.start_time <= datetimetoday.time() <= meeting.end_time and meeting_host.meeting_status == 'FI':
                    # Change the meeting type to ongoing
                    meeting_host.meeting_status = 'ON'
                    meeting_host.save()
                elif meeting.start_time < datetimetoday.time() and meeting_host.meeting_status == 'IN':
                    meeting_host.meeting_status = 'CA'
                    meeting_host.save()
                elif meeting.end_time < datetimetoday.time():
                    meeting_host.meeting_status = 'CO'
                    meeting_host.save()

        '''
        all_meetings = Host.objects.filter(meeting_status='CA')

        for meeting in all_meetings:
            updated_date = meeting.updated_at.date()
            if updated_date == datetimetoday.date()-datetime.timedelta(days=3):
                if meeting.updated_at + datetime.timedelta(days=3) <= datetimetoday:
                    meeting.delete()
        '''
