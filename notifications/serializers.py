from rest_framework import serializers
from notifications.models import Notification


class NotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = ('id', 'title', 'message', 'read', 'notification_type', 'created_at')

class NotificationReadSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = ('read', )