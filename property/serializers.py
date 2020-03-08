import datetime

import pytz
from django.conf import settings
from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from userProfile.models import UserProfile

from .models import Department, Property, Room, RoomBooking


class PropertySerializer(serializers.ModelSerializer):

    class Meta:
        model = Property
        fields = '__all__'


    def create(self, validated_data):
        shared_company_floors = validated_data.pop('shared_company_floors', None)
        
        if isinstance(shared_company_floors, str):
            company_floors = shared_company_floors.split(',')
        else:
            message = 'Use format "[1,2,3,4]" for shared_company_floors'
            raise ValidationError(message)

        floors = []

        for index, company_floor in enumerate(company_floors):
            try:
                if index == 0:
                    company_floor = int(company_floor[1])
                
                if index == len(company_floors) - 1:
                    company_floor = int(company_floor[0])

                floor = int(company_floor)

                if floor not in floors:
                    floors.append(floor)
            except ValueError:
                message = 'Use format "[1,2,3]" for shared_company_floors'
                raise ValidationError(message)
        
        if not floors:
            message = 'There should be a minimum of one floor in a building'
            raise ValidationError(message)
            
        validated_data['shared_company_floors'] = floors

        instance = Property.objects.create(**validated_data)

        return instance

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
        # building = self.context['building']
        user = self.context['user']
        members = []

        # if building == -1 or building is None:
        #     return members

        user_profiles = UserProfile.objects.filter(department=obj)
        for profile in user_profiles:
            if profile.user == user:
                continue
            # profile_pic = profile.profile_pics

            profile_pic = ''
            if profile.profile_pics != '':
                profile_pic = settings.MEDIA_URL+str(profile.profile_pics)

            member = {
                'user_id': profile.user.id,
                'user_name': profile.get_full_name,
                'profile_pics': profile_pic
            }
            members.append(member)

        return members

class RoomSerializer(serializers.ModelSerializer):
    
    class Meta:
        model = Room
        fields = ('__all__')
    
    def create(self, validated_data):
        building_id = validated_data['property']
        building = Property.objects.get(id=building_id.id)
        try:
            floor = int(validated_data['floor'])
        except ValueError:
            message = 'Floor must be integer'
            raise ValidationError(message)

        if floor not in building.shared_company_floors:
            message = 'Floor does not exist on the building'
            raise ValidationError(message)
        
        room = Room.objects.filter(room_number=validated_data['room_number'], floor=validated_data['floor'], property=building)

        if room.exists():
            message = 'Room ' + validated_data['room_number'] + ' already exists on floor ' + validated_data['floor']
            raise ValidationError(message)
        

        instance = Room.objects.create(**validated_data)
        
        return instance
        # Property



class BookedRoomSerializer(serializers.ModelSerializer):
    booked = serializers.SerializerMethodField()

    class Meta:
        model = Room
        fields = ['id', 'room_number', 'floor', 'room_amenity', 'room_type', 'room_capacity', 'is_active', 'booked']
        read_only_fields = ('booked', )

    def get_booked(self, obj):
        # meetings = Details.objects.filter(meeting_date=datetime.date.today(), room=obj)
        now = datetime.datetime.now(pytz.UTC)
        meetings = RoomBooking.objects.filter(booking_date=now.date(), room=obj)

        for meeting in meetings:
            if meeting.booking_start_time.time() <= now.time() <= meeting.booking_end_time.time():
                return True

        return False
