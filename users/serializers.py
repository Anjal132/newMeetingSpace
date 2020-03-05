from django.conf import settings
from rest_framework import serializers

from userProfile.models import UserProfile


class BatchUploadSerializer(serializers.Serializer):
    building = serializers.IntegerField()
    department = serializers.IntegerField()
    file = serializers.FileField()

    def create(self, validated_data):
        return True


class ProfileSerializer(serializers.ModelSerializer):
    office_start_time = serializers.TimeField(format='%H:%M:%S', input_formats=['%I:%M%p', '%I:%M %p', '%H:%M:%S'], required=False, allow_null=True)
    office_end_time = serializers.TimeField(format='%H:%M:%S', input_formats=['%I:%M%p', '%I:%M %p', '%H:%M:%S'], required=False, allow_null=True)

    class Meta:
        model = UserProfile
        fields = '__all__'

    

class ProfileSearchSerializer(serializers.ModelSerializer):

    name = serializers.SerializerMethodField()
    profile_pics = serializers.SerializerMethodField()

    class Meta:
        model = UserProfile
        fields = ('user_id', 'name', 'profile_pics')

    def get_name(self, obj):
        return obj.get_full_name
    
    def get_profile_pics(self, obj):
        profile_pic = ''
        if obj.profile_pics != '':
            profile_pic = settings.MEDIA_URL + str(obj.profile_pics)
        return profile_pic
