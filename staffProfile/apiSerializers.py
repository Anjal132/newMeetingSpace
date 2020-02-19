from rest_framework import serializers

from userProfile.models import UserProfile

class StaffProfileSerializer(serializers.Serializer):
    first_name              = serializers.CharField(max_length=100, required=False)
    middle_name             = serializers.CharField(max_length=100, required=False)
    last_name               = serializers.CharField(max_length=100, required=False)
    internationalization    = serializers.CharField(max_length=2, required=False)
    profile_pics            = serializers.ImageField(required=False)