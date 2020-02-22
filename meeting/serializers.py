from django.core.exceptions import ObjectDoesNotExist
from rest_framework import serializers

from notifications.models import Notification
from userProfile.models import UserProfile
from users.models import User
from utils.otherUtils import send_meeting_mail

from .models import Details, Host, Status


'''
frontend will send Name/email. Upto backend to search for
the id. Also design for firstname + lastname
'''
class StatusSerializer(serializers.ModelSerializer):
    class Meta:
        model = Status
        fields = ('participant',)

class DetailsSerializer(serializers.ModelSerializer):
    start_time = serializers.TimeField(format='%H:%M:%S', input_formats=['%I:%M%p', '%I:%M %p', '%H:%M:%S'])
    end_time = serializers.TimeField(format='%H:%M:%S', input_formats=['%I:%M%p', '%I:%M %p', '%H:%M:%S'])
    
    class Meta:
        model = Details
        fields = '__all__'

    def create(self, validated_data):
        meeting_uid = validated_data['meeting']
        details = Details.objects.create(**validated_data)

        meeting = Host.objects.get(uid=meeting_uid.uid)
        participant_email = meeting.participant_email

        meeting.meeting_status = 'IN'
        meeting.save()

        participants = Status.objects.filter(meeting_host=meeting)
        user_profile = UserProfile.objects.get(user=meeting.host)
        full_name = user_profile.get_full_name
        title = 'Invitation to meeting'
        message = 'You have been invited to Meeting: ' + \
            meeting.title + ' by ' + full_name + '.'

        for participant in participants:
            notification = Notification(user=participant.participant, title=title,
                                        notification_type='meeting', message=message, meeting=details)
            notification.save()

        send_meeting_mail(participant_email, meeting, details)

        return details


class MeetingHostSerializer(serializers.ModelSerializer):
    meeting_to_participant = serializers.JSONField()
    
    class Meta:
        model = Host
        fields = ('uid', 'title', 'agenda', 'duration', 'start_date',
                  'end_date', 'type', 'meeting_to_participant', 'timezone')
        read_only_fields = ('uid', )

    def create(self, validated_data):
        participant_data = validated_data.pop('meeting_to_participant')
        validated_data['host'] = self.context['host']
        host = Host.objects.create(**validated_data)

        send_email_to_other_participants = []

        for participants in participant_data:
            participant = participants['participant']
            try:
                participant = int(participant)
                userid = User.objects.get(id=participant)
                Status.objects.create(meeting_host=host, participant=userid)
            except ValueError:
                send_email_to_other_participants.append(participant)
            except ObjectDoesNotExist:
                print('Invalid Participant ID')

        host.participant_email = send_email_to_other_participants
        host.save()

        return host

    def update(self, instance, validated_data):
        participant_data = validated_data.pop('meeting_to_participant')
        validated_data['host'] = self.context['host']

        send_email_to_other_participants = []

        instance.title = validated_data['title']
        instance.agenda = validated_data['agenda']
        instance.duration = validated_data['duration']
        instance.start_date = validated_data['start_date']
        instance.end_date = validated_data['end_date']
        instance.type = validated_data['type']
        instance.timezone = validated_data['timezone']

        Status.objects.filter(meeting_host=instance).delete()

        for participants in participant_data:
            participant = participants['participant']

            try:
                participant = int(participant)
                userid = User.objects.get(id=participant)
                Status.objects.create(meeting_host=instance, participant=userid)
            except ValueError:
                send_email_to_other_participants.append(participant)
            except ObjectDoesNotExist:
                print('Invalid Participant ID')

        instance.participant_email = send_email_to_other_participants
        instance.save()

        return instance
