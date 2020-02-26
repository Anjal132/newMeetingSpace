import datetime

from rest_framework import serializers

from meeting.models import Details

from .models import Department, Property, Room
from userProfile.models import UserProfile


class PropertySerializer(serializers.ModelSerializer):

    class Meta:
        model = Property
        fields = '__all__'


class DepartmentSerializer(serializers.ModelSerializer):

    class Meta:
        model = Department
        fields = '__all__'

class DepartmentDetailSerializer(serializers.ModelSerializer):
    members = serializers.SerializerMethodField()
    class Meta:
        model = Department
        fields = ['id', 'department_name', 'members']
    
    def get_members(self, obj):
        building = self.context['building']
        user = self.context['user']
        members = []

        if building == -1 or building is None:
            return members

        user_profiles = UserProfile.objects.filter(department=obj, building=building)
        for profile in user_profiles:
            if profile.user == user:
                continue

            member = {
                'user_id': profile.user.id,
                'user_name': profile.get_full_name
            }
            members.append(member)

        return members

class RoomSerializer(serializers.ModelSerializer):
    
    class Meta:
        model = Room
        fields = ('__all__')


class BookedRoomSerializer(serializers.ModelSerializer):
    booked = serializers.SerializerMethodField()

    class Meta:
        model = Room
        fields = ['id', 'room_number', 'floor', 'room_amenity', 'room_type', 'room_capacity', 'is_active', 'booked']

    def get_booked(self, obj):
        meetings = Details.objects.filter(meeting_date=datetime.date.today(), room=obj)
        rightnow = datetime.datetime.now()

        for meeting in meetings:
            if meeting.start_time <= rightnow.time() <= meeting.end_time:
                return True

        return False
