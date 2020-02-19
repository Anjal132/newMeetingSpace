from rest_framework import serializers
from userProfile.models import UserProfile


class BatchUploadSerializer(serializers.Serializer):
    building = serializers.IntegerField()
    department = serializers.IntegerField()
    file = serializers.FileField()

    def create(self, validated_data):
        return True


class ProfileSerializer(serializers.ModelSerializer):

    class Meta:
        model = UserProfile
        fields = '__all__'


class ProfileSearchSerializer(serializers.ModelSerializer):

    name = serializers.SerializerMethodField()
    # profile_picture = serializers.SerializerMethodField()


    class Meta:
        model = UserProfile
        fields = ('user_id', 'name', 'profile_pics')

    def get_name(self, obj):
        return obj.get_full_name

    # def get_profile_picture(self, obj):
    #     print(obj.profile_pics)
    #     return obj.profile_pics
        