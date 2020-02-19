from rest_framework import serializers
from .models import Google


class GoogleCalendarSerializer(serializers.ModelSerializer):
    class Meta:
        model = Google
        fields = '__all__'