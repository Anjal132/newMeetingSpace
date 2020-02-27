import datetime

from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from meeting.models import Details
from userProfile.models import UserProfile

from .models import Department, Property, Room


class PropertySerializer(serializers.ModelSerializer):

    class Meta:
        model = Property
        fields = '__all__'


    def create(self, validated_data):
        shared_company_floors = validated_data.pop('shared_company_floors', None)
        company_floors = shared_company_floors.split(',')
        floors = []

        for index, company_floor in enumerate(company_floors):
            try:
                if index == 0:
                    company_floor = int(company_floor[1])
                
                if index == len(company_floors) - 1:
                    company_floor = int(company_floor[0])

                floor = int(company_floor)
                floors.append(floor)
            except ValueError:
                continue
        
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

    def get_booked(self, obj):
        meetings = Details.objects.filter(meeting_date=datetime.date.today(), room=obj)
        rightnow = datetime.datetime.now()

        for meeting in meetings:
            if meeting.start_time <= rightnow.time() <= meeting.end_time:
                return True

        return False
