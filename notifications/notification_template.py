from meeting.models import Details, Status
from notifications.models import Notification
from utils.otherUtils import canceled_meeting_mail

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
    for participant in participants:
        title = kwargs['title']
        message = kwargs['message']
        notification_type = 'meeting'
        host = kwargs['host']
        Notification.objects.create(title=title, message=message, notification_type=notification_type,
                                    meeting=details, user=participant.participant, notification_by=host)


def create_notification_host(meeting):
    participants = Status.objects.filter(meeting_host=meeting)
    details = Details.objects.get(meeting=meeting)
    kwargs = {'host': meeting.host}

    if meeting.meeting_status == 'IN':
        kwargs['title'] = 'Invitation to meeting'
        kwargs['message'] = ' has invited you to '
        after_meeting_status_change(participants, details, **kwargs)

    elif meeting.meeting_status == 'FI':
        kwargs['title'] = 'Meeting has been finalized'
        kwargs['message'] = ' has finalized meeting '
        after_meeting_status_change(participants, details, **kwargs)

    elif meeting.meeting_status == 'CA':
        kwargs['title'] = 'Meeting has been cancelled'
        kwargs['message'] = ' has cancelled '
        after_meeting_status_change(participants, details, **kwargs)
        canceled_meeting_mail(meeting, details)
        
    elif meeting.meeting_status == 'CO':
        participants = Status.objects.filter(meeting_host=meeting, participant_status='AC')
        kwargs['title'] = 'Meeting has been completed'
        kwargs['message'] = ' has succesfully hosted meeting '
        after_meeting_status_change(participants, details, **kwargs)
