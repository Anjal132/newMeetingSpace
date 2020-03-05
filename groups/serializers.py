from django.conf import settings
from rest_framework import serializers

from groups.models import Group
from userProfile.models import UserProfile
from users.serializers import ProfileSearchSerializer



class GroupSerializer(serializers.ModelSerializer):
    class Meta:
        model = Group
        fields = '__all__'
        read_only_fields = ('leader', )
    
    def create(self, validated_data):
        group_members = validated_data.pop('group_members')
        validated_data['leader'] = self.context['leader']
        group = Group.objects.create(**validated_data)
        group.group_members.set(group_members)

        return group


class GroupDetailSerializer(serializers.ModelSerializer):
    group_members = serializers.SerializerMethodField()

    class Meta:
        model = Group
        fields = ['id', 'group_name', 'group_members']
    
    def get_group_members(self, obj):
        user_profiles = UserProfile.objects.filter(user__in=obj.group_members.all())
        users = []
        
        for profile in user_profiles:
            full_name = profile.get_full_name

            if full_name is None:
                full_name = ''
            
            profile_pic = ''
            if profile.profile_pics != '':
                profile_pic = settings.MEDIA_URL+str(profile.profile_pics)

            user = {
                'user_id': profile.user.id,
                'user_name': full_name,
                'profile_pics': profile_pic
            }
            users.append(user)
        return users
