import pytz
import datetime
from django.conf import settings
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import send_mail
from django.db import connection
from django.template.loader import render_to_string
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode

from organization.models import Organization
from userProfile.models import UserProfile

# from users.models import User

def send_meeting_mail(participant_list, meeting, details):
    full_name = UserProfile.objects.get(user=meeting.host).get_full_name
    schema_name = Organization.objects.get(schema_name=connection.get_schema())

    mail_subject = 'Invitation to ' + meeting.title
    
    meeting_start_time = datetime.datetime.combine(details.meeting_date, details.start_time)
    meeting_end_time = datetime.datetime.combine(details.meeting_date, details.end_time)

    meeting_start_time = meeting_start_time.astimezone(pytz.timezone(meeting.timezone))
    meeting_end_time = meeting_end_time.astimezone(pytz.timezone(meeting.timezone))

    message = render_to_string('send_meeting_email.html', {
        'meeting_title': meeting.title,
        'meeting_start_time': meeting_start_time.strftime('%H:%M%p'),
        'meeting_end_time': meeting_end_time.strftime('%H:%M%p'),
        'meeting_room': details.room.room_number,
        'floor': details.room.floor,
        'meeting_host': full_name,
        'company_name': schema_name.name,
        'property_location': details.room.property.name,
        'meeting_date': details.meeting_date,
        'street': details.room.property.street,
        'city': details.room.property.city,
        'country': details.room.property.country
    })

    send_mail(mail_subject, message, 'admin@meetingspace.com', participant_list, fail_silently=False)


def canceled_meeting_mail(meeting, details):
    full_name = UserProfile.objects.get(user=meeting.host).get_full_name
    schema_name = Organization.objects.get(schema_name=connection.get_schema())

    mail_subject = '{0} has been cancelled'.format(meeting.title)
    
    meeting_start_time = datetime.datetime.combine(details.meeting_date, details.start_time)
    meeting_end_time = datetime.datetime.combine(details.meeting_date, details.end_time)

    meeting_start_time = meeting_start_time.astimezone(pytz.timezone(meeting.timezone))
    meeting_end_time = meeting_end_time.astimezone(pytz.timezone(meeting.timezone))

    message = render_to_string('send_meeting_email.html', {
        'meeting_title': meeting.title,
        'meeting_start_time': meeting_start_time.strftime('%H:%M%p'),
        'meeting_end_time': meeting_end_time.strftime('%H:%M%p'),
        'meeting_room': details.room.room_number,
        'floor': details.room.floor,
        'meeting_host': full_name,
        'company_name': schema_name.name,
        'property_location': details.room.property.name,
        'meeting_date': details.meeting_date,
        'street': details.room.property.street,
        'city': details.room.property.city,
        'country': details.room.property.country
    })

    send_mail(mail_subject, message, 'admin@meetingspace.com', meeting.participant_email, fail_silently=False)



def send_mail_admin(admin_list, company_name):
    
    for admin in admin_list:

        uid = urlsafe_base64_encode(force_bytes(admin.uid))
        token = default_token_generator.make_token(admin)

        mail_subject = 'Attention!, Email Verification (Meeting Space)'

        message = render_to_string('confirm_email_admin.html', {
            'company': company_name,
            'domain': settings.FRONTEND_URL + '/verify/' + uid + '/' + token,
        })

        send_mail(mail_subject, message, 'admin@meetingspace.com',
                    [admin.email], fail_silently=False)

def send_password_reset_email(user):

    uid = urlsafe_base64_encode(force_bytes(user.uid))
    token = default_token_generator.make_token(user)

    mail_subject = 'Attention!, Email Verification (Meeting Space)'

    message = render_to_string('reset_email.html', {
        'domain': settings.FRONTEND_URL + '/reset_password/' + uid + '/' + token,
    })

    send_mail(mail_subject, message, 'admin@meetingspace.com',
                [user.email], fail_silently=False)

def send_mail_employee(user, organization):

    
    uid = urlsafe_base64_encode(force_bytes(user.uid))
    token = default_token_generator.make_token(user)

    mail_subject = 'Attention!, Email Verification (Meeting Space)'

    message = render_to_string('confirm_email.html', {
        'company': organization.name,
        'domain': settings.FRONTEND_URL + '/verify/' + uid + '/' + token,
    })

    send_mail(mail_subject, message, 'admin@meetingspace.com',
                [user.email], fail_silently=False)
