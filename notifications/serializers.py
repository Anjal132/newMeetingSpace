import datetime

import pytz
import timeago
from django.conf import settings
from rest_framework import serializers

from notifications.models import Notification
from userProfile.models import UserProfile


class NotificationSerializer(serializers.ModelSerializer):
    name = serializers.SerializerMethodField()
    meeting_title = serializers.SerializerMethodField()
    meeting = serializers.SerializerMethodField()
    profile_pics = serializers.SerializerMethodField()
    meeting_date = serializers.SerializerMethodField()
    start_time = serializers.SerializerMethodField()
    end_time = serializers.SerializerMethodField()
    timeago = serializers.SerializerMethodField()

    class Meta:
        model = Notification
        fields = ('id', 'name', 'message', 'notification_type', 'meeting', 'meeting_title', 'profile_pics', 'meeting_date', 'start_time', 'end_time', 'timeago')
    
    def get_meeting_date(self, obj):
        return obj.meeting.meeting_date
    
    def get_timeago(self, obj):
        created_at = obj.created_at
        now = datetime.datetime.now(pytz.UTC)

        tago = timeago.format(created_at, now)
        tago = tago.replace(" ago", "")
        return tago
    
    def get_start_time(self, obj):
        return obj.meeting.start_time.strftime('%I:%M %p')
    
    def get_end_time(self, obj):
        return obj.meeting.end_time.strftime('%I:%M %p')

    def get_name(self, obj):
        profile = UserProfile.objects.get(user=obj.notification_by)
        return profile.get_full_name
    
    def get_meeting_title(self, obj):
        return obj.meeting.meeting.title
    
    def get_meeting(self, obj):
        return obj.meeting.meeting.uid
    
    def get_profile_pics(self, obj):
        profile = UserProfile.objects.get(user=obj.notification_by)
        profile_pic = ''

        if profile.profile_pics != '':
            profile_pic = settings.MEDIA_URL + str(profile.profile_pics)
            
        return profile_pic


class NotificationReadSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = ('read', )
