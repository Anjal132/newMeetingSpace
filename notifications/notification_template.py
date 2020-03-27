import json

import requests

from meeting.models import Details, Status
from notifications.models import FCMRegistrationToken, Notification
from notifications.utils import get_access_token
from utils.otherUtils import canceled_meeting_mail
from userProfile.models import UserProfile

BASE_URL = 'http://a64a43e2.ngrok.io/media/{0}'
CLOUD_MESSAGING_URL = 'https://fcm.googleapis.com/v1/{0}/messages:send'
PROJECT_ID = 'projects/meetingspace-271809'

FINAL_URL = CLOUD_MESSAGING_URL.format(PROJECT_ID)

def after_participant_status_change(meeting, participant, **kwargs):
    title = kwargs['title']
    message = kwargs['message']
    notification_type = 'meeting'
    Notification.objects.create(title=title, message=message, notification_type=notification_type,
                                meeting=meeting, user=meeting.meeting.host, notification_by=participant)

def create_notification_participant(status, user, meeting):
    meeting_details = Details.objects.get(meeting=meeting)
    if status == 'AC':
        kwargs = {
            'title': 'Invitation accepted',
            'message': ' has accepted your invitation to '
        }
        after_participant_status_change(meeting_details, user, **kwargs)
    elif status == 'DE':
        kwargs = {
            'title': 'Invitation declined',
            'message': ' has declined your invitation to '
        }
        after_participant_status_change(meeting_details, user, **kwargs)
    elif status == 'PO':
        kwargs = {
            'title': 'Postpone requested',
            'message': ' has requested you to postpone meeting '
        }
        after_participant_status_change(meeting_details, user, **kwargs)


def after_meeting_status_change(participants, details, **kwargs):
    headers = {
        'Authorization': 'Bearer {0}'.format(get_access_token()),
        'Content-Type': 'application/json; UTF-8'
    }
    title = kwargs['title']
    message = kwargs['message']
    notification_type = 'meeting'
    
    host = kwargs['host']

    host_profile = UserProfile.objects.get(user=host)
    pushmessage = kwargs['pushmessage'].format(host_profile.get_full_name, details.meeting.title)

    profile_pic = ''
    if str(host_profile.profile_pics) != '':
        profile_pic = BASE_URL.format(str(host_profile.profile_pics))

    
    for participant in participants:
        Notification.objects.create(title=title, message=message, notification_type=notification_type,
                                    meeting=details, user=participant.participant, notification_by=host)
        
        registration_tokens = FCMRegistrationToken.objects.filter(user=participant.participant)

        if registration_tokens.exists():
            for token in registration_tokens:
                data = {
                    "message": {
                        "android": {
                            "notification": {
                                "title": title,
                                "body": pushmessage,
                                "image": profile_pic,
                                "click_action": "com.t4tech.meetingspace_TARGET_NOTIFICATION"
                            }
                        },
                        "token": str(token.token),
                        "data": {
                            "meeting_id": str(details.meeting.uid),
                            "host": "False",
                            "meeting_status": details.meeting.meeting_status
                        }
                    }
                }
            
                resp = requests.post(FINAL_URL, data=json.dumps(data), headers=headers)
                print(resp.json())
        
        print(profile_pic)

def create_notification_host(meeting):
    participants = Status.objects.filter(meeting_host=meeting)
    details = Details.objects.get(meeting=meeting)
    kwargs = {'host': meeting.host}

    if meeting.meeting_status == 'IN':
        kwargs['title'] = 'Invitation to meeting'
        kwargs['message'] = ' has invited you to '
        kwargs['pushmessage'] = '{0} has invited you to meeting {1}.'
        after_meeting_status_change(participants, details, **kwargs)

    elif meeting.meeting_status == 'FI':
        kwargs['title'] = 'Meeting has been finalized'
        kwargs['message'] = ' has finalized meeting '
        kwargs['pushmessage'] = '{0} has finalized meeting {1}.'
        after_meeting_status_change(participants, details, **kwargs)

    elif meeting.meeting_status == 'CA':
        kwargs['title'] = 'Meeting has been cancelled'
        kwargs['message'] = ' has cancelled '
        kwargs['pushmessage'] = '{0} has cancelled meeting {1}.'
        after_meeting_status_change(participants, details, **kwargs)
        canceled_meeting_mail(meeting, details)

    elif meeting.meeting_status == 'CO':
        participants = Status.objects.filter(meeting_host=meeting, participant_status='AC')
        kwargs['title'] = 'Meeting has been completed'
        kwargs['message'] = ' has succesfully hosted meeting '
        kwargs['pushmessage'] = 'Meeting {1}, hosted by {0}, has been successfully completed.'
        after_meeting_status_change(participants, details, **kwargs)
