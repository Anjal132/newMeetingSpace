import datetime

import pytz
from django.core.exceptions import ObjectDoesNotExist, ValidationError
from pytz.exceptions import UnknownTimeZoneError
from rest_framework import serializers

from notifications.models import Notification
from userProfile.models import UserProfile
from users.models import User
from utils.otherUtils import send_meeting_mail

from .models import Details, Host, Status


class HostSerializer(serializers.ModelSerializer):
    duration = serializers.SerializerMethodField()
    class Meta:
        model = Host
        fields = ['uid', 'title', 'agenda', 'duration', 'start_date', 'end_date', 'type', 'participant_email', 'participant']
    
    def get_duration(self, obj):
        return int(obj.duration.seconds / 60)



class DetailsSerializer(serializers.ModelSerializer):
    start_time = serializers.TimeField(format='%H:%M:%S', input_formats=['%I:%M%p', '%I:%M %p', '%H:%M:%S'])
    end_time = serializers.TimeField(format='%H:%M:%S', input_formats=['%I:%M%p', '%I:%M %p', '%H:%M:%S'])
    
    class Meta:
        model = Details
        fields = '__all__'

    def create(self, validated_data):
        print('Create')
        meeting_uid = validated_data['meeting']        
        details = Details.objects.create(**validated_data)

        meeting = Host.objects.get(uid=meeting_uid.uid)
        participant_email = meeting.participant_email

        meeting.meeting_status = 'IN'
        meeting.save()

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
        meeting_host = self.context['host']
        validated_data['host'] = meeting_host
        tzone = validated_data['timezone']

        start_date = validated_data['start_date']
        end_date = validated_data['end_date']

        try:
            tzone = pytz.timezone(tzone)
        except pytz.exceptions.UnknownTimeZoneError:
            message = 'Invalid timezone'
            raise ValidationError(message)

        current_date = datetime.datetime.now(tz=tzone)

        if end_date < current_date.date() or end_date < start_date:
            message = 'Invalid end date'
            raise ValidationError(message)
            
        if start_date < current_date.date():
            validated_data['start_date'] = current_date.date()

        host = Host.objects.create(**validated_data)

        send_email_to_other_participants = []

        for participants in participant_data:
            participant = participants['participant']
            try:
                participant = int(participant)
                userid = User.objects.get(id=participant)
                participant_meeting = Status.objects.filter(meeting_host=host, participant=userid)

                if not participant_meeting.exists():
                    if host.host.id == userid.id:
                        message = 'Cannot invite yourself to the meeting'
                        raise ValidationError(message)
                    
                    if not userid.is_active or not userid.is_verified:
                        message = 'Cannot invite inactive/unverfied users'
                        raise ValidationError(message)

                    if userid.temp_name != host.host.temp_name:
                        message = 'User does not exist'
                        raise ValidationError(message)

                    Status.objects.create(meeting_host=host, participant=userid)
            except ValueError:
                if participant in send_email_to_other_participants:
                    continue

                send_email_to_other_participants.append(participant)
            except ObjectDoesNotExist:
                message = 'User does not exist'
                raise ValidationError(message)

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
                participant_meeting = Status.objects.filter(meeting_host=instance, participant=userid)

                if not participant_meeting.exists():
                    Status.objects.create(meeting_host=instance, participant=userid)
            except ValueError:
                if participant in send_email_to_other_participants:
                    continue
                
                send_email_to_other_participants.append(participant)
            except ObjectDoesNotExist:
                print('Invalid Participant ID')

        instance.participant_email = send_email_to_other_participants
        instance.save()

        return instance