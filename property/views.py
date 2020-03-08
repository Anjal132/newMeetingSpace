import datetime

import pytz
import timeago
from django.core.exceptions import ObjectDoesNotExist, ValidationError
from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from meeting.models import Details
from pagination.pagination import SmallResultsSetPagination
from permission.permissions import IsCompanyAdmin, IsEmployee
from userProfile.models import UserProfile
from utils.utils import get_user

from .models import Department, Property, Room, RoomBooking
from .serializers import (BookedRoomSerializer, DepartmentDetailSerializer,
                          DepartmentSerializer, PropertySerializer,
                          RoomSerializer)


'''
Get all available rooms
'''
UTC_TIMEZONE = 'UTC'


class AvailableRoomsAPIView(generics.ListAPIView):
    permission_classes = [IsAuthenticated, IsEmployee]
    serializer_class = RoomSerializer
    pagination_class = SmallResultsSetPagination

    def get_queryset(self):
        user = get_user(self.request)
        now = datetime.datetime.now(pytz.UTC)

        floor = self.request.query_params.get('floor', None)
        booked = self.request.query_params.get('booked', None)
        room_type_query = self.request.query_params.get('roomType', None)

        if booked is None:
            return Room.objects.none()

        if not booked == 'booked' and not booked == 'available':
            return Room.objects.none()

        user_profile = UserProfile.objects.get(user=user)
        rooms_in_user_building = UserProfile.objects.filter(
            building=user_profile.building)

        try:
            building = Property.objects.get(id=user_profile.building.id)
        except ObjectDoesNotExist:
            return Room.objects.none()
        except AttributeError:
            return Room.objects.none()

        if floor is None:
            floor = building.shared_company_floors
        else:
            try:
                floor = int(floor)
                if floor not in building.shared_company_floors:
                    return Room.objects.none()
                floor = [floor]
            except ValueError:
                return Room.objects.none()

        room_type = []
        room_type_list = ['CR', 'MR', 'PO', 'DH']
        if room_type_query is None:
            room_type = room_type_list
        elif not room_type_query in room_type_list:
            return Room.objects.none()

        room_type.append(room_type_query)

        exclude_rooms = []

        for user_room in rooms_in_user_building:
            if user_room.room is not None:
                exclude_rooms.append(user_room.room.id)

        all_rooms = Room.objects.filter(
            property=user_profile.building).exclude(id__in=exclude_rooms)

        booked_rooms = []
        for room in all_rooms:
            # meetings = Details.objects.filter(
            #     meeting_date=now.date(), room=room)
            meetings = RoomBooking.objects.filter(booking_date=now.date(), room=room)

            for meeting in meetings:
                current_time = datetime.datetime.now(pytz.UTC)
                if meeting.booking_start_time <= current_time <= meeting.booking_end_time:
                    booked_rooms.append(meeting.room.id)
                    exclude_rooms.append(meeting.room.id)

        if booked == 'booked':
            return Room.objects.filter(property=user_profile.building, room_type__in=room_type, floor__in=floor, id__in=booked_rooms, is_active=True).order_by('floor', 'room_number')
        return Room.objects.filter(property=user_profile.building, room_type__in=room_type, floor__in=floor, is_active=True).exclude(id__in=exclude_rooms).order_by('floor', 'room_number')


class AllRoomsAPIView(generics.ListAPIView):
    permission_classes = [IsAuthenticated, IsEmployee]
    serializer_class = BookedRoomSerializer
    pagination_class = SmallResultsSetPagination

    def get_queryset(self):
        property_id = self.request.query_params.get('property', None)
        active_rooms = self.request.query_params.get('active', None)
        room_type = self.request.query_params.get('roomType', None)
        floor = self.request.query_params.get('floor', None)

        if property_id is None:
            return Room.objects.none()

        try:
            buildings = Property.objects.get(id=property_id)
        except ObjectDoesNotExist:
            return Room.objects.none()

        if floor is None:
            floor = buildings.shared_company_floors
        else:
            try:
                floor = int(floor)

                if floor not in buildings.shared_company_floors:
                    return Room.objects.none()

                floor = [floor]
            except ValueError:
                return Response({'Message': 'Floor must be integer'}, status=status.HTTP_400_BAD_REQUEST)

        room_type_list = ['CR', 'MR', 'PO', 'DH', 'BR']
        active_rooms_list = ['active', 'inactive']

        if active_rooms is not None:
            is_active = False

            if active_rooms == 'active':
                is_active = True

        if active_rooms is not None and room_type is not None:
            if not active_rooms in active_rooms_list or not room_type in room_type_list:
                return Room.objects.none()

            return Room.objects.filter(property=property_id, room_type=room_type, is_active=is_active, floor__in=floor).order_by('floor', 'room_number')

        if room_type is not None:
            if room_type in room_type_list:
                return Room.objects.filter(property=property_id, room_type=room_type, floor__in=floor).order_by('floor', 'room_number')
            return Room.objects.none()

        if active_rooms is not None:
            if active_rooms in active_rooms_list:
                return Room.objects.filter(property=property_id, is_active=is_active, floor__in=floor).order_by('floor', 'room_number')
            return Room.objects.none()

        return Room.objects.filter(property=property_id, floor__in=floor).order_by('floor', 'room_number')


class AllRoomsAPIViewWithoutPagination(generics.ListAPIView):
    permission_classes = [IsAuthenticated, IsEmployee]
    serializer_class = BookedRoomSerializer

    def get_queryset(self):
        property_id = self.request.query_params.get('property', None)
        active_rooms = self.request.query_params.get('active', None)
        room_type = self.request.query_params.get('roomType', None)
        floor = self.request.query_params.get('floor', None)

        if property_id is None:
            return Room.objects.none()

        try:
            buildings = Property.objects.get(id=property_id)
        except ObjectDoesNotExist:
            return Room.objects.none()

        if floor is None:
            floor = buildings.shared_company_floors
        else:
            try:
                floor = int(floor)

                if floor not in buildings.shared_company_floors:
                    return Room.objects.none()

                floor = [floor]
            except ValueError:
                return Response({'Message': 'Floor must be integer'}, status=status.HTTP_400_BAD_REQUEST)

        room_type_list = ['CR', 'MR', 'PO', 'DH', 'BR']
        active_rooms_list = ['active', 'inactive']

        if active_rooms is not None:
            is_active = False

            if active_rooms == 'active':
                is_active = True

        if active_rooms is not None and room_type is not None:
            if not active_rooms in active_rooms_list or not room_type in room_type_list:
                return Room.objects.none()

            return Room.objects.filter(property=property_id, room_type=room_type, is_active=is_active, floor__in=floor).order_by('floor', 'room_number')

        if room_type is not None:
            if room_type in room_type_list:
                return Room.objects.filter(property=property_id, room_type=room_type, floor__in=floor).order_by('floor', 'room_number')
            return Room.objects.none()

        if active_rooms is not None:
            if active_rooms in active_rooms_list:
                return Room.objects.filter(property=property_id, is_active=is_active, floor__in=floor).order_by('floor', 'room_number')
            return Room.objects.none()

        return Room.objects.filter(property=property_id, floor__in=floor).order_by('floor', 'room_number')


'''
Add property to an organization. Get all the properties of an organization.
'''


class PropertyAddView(generics.ListCreateAPIView):
    permission_classes = (IsAuthenticated, IsCompanyAdmin,)
    serializer_class = PropertySerializer
    pagination_class = SmallResultsSetPagination

    def get_queryset(self):
        if self.request.method == 'GET':
            building_status = self.request.query_params.get('status', None)

            if building_status is not None and building_status == 'available':
                return Property.objects.exclude(is_available='SD').order_by('id')

            if building_status is not None:
                if building_status == 'unavailable':
                    return Property.objects.filter(is_available='SD').order_by('id')
                return Property.objects.none()

            return Property.objects.all().order_by('id')
        return Property.objects.all().order_by('id')


'''
Get and Edit property details.
'''


class PropertyDetailAPIView(generics.RetrieveUpdateAPIView):
    permission_classes = (IsAuthenticated, IsCompanyAdmin)
    queryset = Property.objects.all()
    serializer_class = PropertySerializer

    def get_queryset(self):
        print(self.request.data)
        return Property.objects.all()


'''
Add departments to a property.
'''


class DepartmentView(generics.ListCreateAPIView):
    permission_classes = (IsAuthenticated, IsCompanyAdmin,)
    queryset = Department.objects.all()
    serializer_class = DepartmentSerializer


class DepartmentMembersView(generics.ListAPIView):
    permission_classes = [IsAuthenticated, IsCompanyAdmin]
    serializer_class = DepartmentDetailSerializer

    def get_queryset(self):
        try:
            department_id = self.kwargs['pk']
            return Department.objects.filter(id=department_id)
        except KeyError:
            return Department.objects.none()
    
    def get_serializer_context(self):
        user = get_user(self.request)
        return {'user': user}

class DepartmentDetailView(generics.ListAPIView):
    permission_classes = [IsAuthenticated, IsEmployee]
    serializer_class = DepartmentDetailSerializer

    def list(self, request):
        try:
            user = get_user(request)
            profile = UserProfile.objects.get(user=user)

            # building = -1
            # if profile.building is not None:
            #     building = profile.building

            # context = {'building': building, 'user': user}
            context = {'user': user}

            queryset = self.get_queryset()
            serializer = DepartmentDetailSerializer(
                queryset, many=True, context=context)
            return Response(serializer.data)
        except ValidationError:
            return Response({'Message': 'Validation Error. Please retry later'}, status=status.HTTP_400_BAD_REQUEST)
        except ObjectDoesNotExist:
            return Response({'Message': 'User Does not exist'}, status=status.HTTP_400_BAD_REQUEST)

    def get_queryset(self):
        try:
            user = get_user(self.request)
            user_profile = UserProfile.objects.get(user=user)

            if user_profile.department is None:
                return Department.objects.none()
            return Department.objects.filter(id=user_profile.department.id)
        except ObjectDoesNotExist:
            return Department.objects.none()


'''
Add rooms to a property and get all the rooms in an organization.
'''


class RoomAddView(generics.CreateAPIView):
    permission_classes = (IsAuthenticated, IsCompanyAdmin,)
    queryset = Room.objects.all()
    serializer_class = RoomSerializer


'''
Get all active properties and the respective departments in the property.
Returns department as nested JSON.
'''


class AllBuildingAllDepartmentView(APIView):
    permission_classes = (IsAuthenticated, IsEmployee)

    def get(self, request):
        buildings = Property.objects.all()
        departments = Department.objects.all()

        property_serializer = PropertySerializer(buildings, many=True)
        department_serializer = DepartmentSerializer(departments, many=True)

        buildings = []
        for data in property_serializer.data:
            if data['is_available'] == 'SD':
                continue

            building = {
                'id': data['id'],
                'name': data['name'],
                'shared_company_floors': data['shared_company_floors']
            }
            buildings.append(building)

        return Response({
            'buildings': buildings,
            'departments': department_serializer.data},
            status=status.HTTP_200_OK)


class RoomDetailsAPIView(APIView):
    permission_classes = [IsAuthenticated, IsEmployee]

    def get(self, request, *args, **kwargs):
        user = get_user(request)
        room_id = self.kwargs['pk']
        room = Room.objects.get(id=room_id)
        meeting_details = Details.objects.filter(room=room)

        booked = False
        current_time = datetime.datetime.now(tz=pytz.UTC)
        meetings = RoomBooking.objects.filter(
            booking_date=current_time.date(), room=room)

        for meeting in meetings:
            if meeting.booking_start_time < current_time <= meeting.booking_end_time:
                booked = True

        room_details = {
            'room_number': room.room_number,
            'floor': room.floor,
            'building': room.property.id,
            'building_name': room.property.name,
            'room_type': room.room_type,
            'room_amenity': room.room_amenity,
            'room_capacity': room.room_capacity,
            'active': room.is_active,
            'booked': booked
        }

        meeting = []
        for meeting_detail in meeting_details:
            host_profile = UserProfile.objects.get(
                user=meeting_detail.meeting.host)

            if meeting_detail.meeting.type == 'PV':
                meetings = {
                    'type': meeting_detail.meeting.type,
                    'hosted_by': host_profile.get_full_name,
                    'date': meeting_detail.meeting_date,
                    'start_time': meeting_detail.start_time.strftime('%I:%M %p'),
                    'end_time': meeting_detail.end_time.strftime('%I:%M %p'),
                    'host': meeting_detail.meeting.host == user
                }
            else:
                meetings = {
                    'type': meeting_detail.meeting.type,
                    'hosted_by': host_profile.get_full_name,
                    'date': meeting_detail.meeting_date,
                    'start_time': meeting_detail.start_time.strftime('%I:%M %p'),
                    'end_time': meeting_detail.end_time.strftime('%I:%M %p'),
                    'title': meeting_detail.meeting.title,
                    'agenda': meeting_detail.meeting.agenda,
                    'host': meeting_detail.meeting.host == user
                }

            meeting.append(meetings)

        room_details['meetings'] = meeting

        return Response({"Room": room_details}, status=status.HTTP_200_OK)


class DepartmentUpdateDeleteView(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [IsAuthenticated, IsCompanyAdmin]
    serializer_class = DepartmentSerializer
    queryset = Department.objects.all()


class RoomUpdateAPIView(generics.UpdateAPIView):
    permission_classes = [IsAuthenticated, IsCompanyAdmin]
    serializer_class = BookedRoomSerializer
    queryset = Room.objects.all()


class BookRoomAPIView(APIView):
    permission_classes = [IsAuthenticated, IsEmployee]

    def get(self, request, *args, **kwargs):
        try:
            room_id = kwargs['room_id']
            # room = Room.objects.get(id=room_id)

            now = datetime.datetime.now(pytz.UTC)
            print(now.tzinfo)

            meetings_on_room = RoomBooking.objects.filter(
                room=room_id, booking_date__gte=now.date()).order_by('booking_date', 'booking_start_time')
            for meeting in meetings_on_room:
                if meeting.booking_start_time < now < meeting.booking_end_time:
                    if meeting.meeting is not None and meeting.meeting.meeting_status == 'CO':
                        break
                    time_ago = timeago.format(meeting.booking_end_time, now)
                    message = 'A meeting is ongoing. The room will be avaible {0}.'.format(
                        time_ago)
                    return Response({'Message': message}, status=status.HTTP_400_BAD_REQUEST)

            meetings_on_room = RoomBooking.objects.filter(
                room=room_id, booking_start_time__gte=now).order_by('booking_date', 'booking_start_time')

            if meetings_on_room.exists():
                duration = meetings_on_room[0].booking_start_time - now

                duration_in_minutes = int(duration.seconds/60)
                time_ago = timeago.format(meetings_on_room[0].booking_start_time, now)

                if duration_in_minutes <= 5:
                    message = 'The room will be booked {0}. You cannot book the room now'.format(
                        time_ago)
                    return Response({'Message': message}, status=status.HTTP_400_BAD_REQUEST)

                if 'in' in time_ago:
                    time_ago = time_ago.replace('in', 'for')
                
                message = 'The room can be booked {0}.'.format(time_ago)
                return Response({'Message': message}, status=status.HTTP_200_OK)
        except KeyError:
            return Response({'Message': 'room_id required in the url'}, status=status.HTTP_400_BAD_REQUEST)
        return Response({'Message': 'The room is available for booking'}, status=status.HTTP_200_OK)

    def post(self, request, *args, **kwargs):
        user = get_user(request)
        now = datetime.datetime.now(pytz.UTC)
        print(now)

        print(request.data)

        try:
            duration = request.data['duration']
            room_id = kwargs['room_id']
            print(duration)
            print(room_id)

            participants = []

            if 'participants' in request.data:
                participants = request.data['participants']

            duration = int(duration)
            room_id = int(room_id)

            new_booking_end_time = now + datetime.timedelta(minutes=duration)

            room = Room.objects.get(id=room_id)
            booked_rooms = RoomBooking.objects.filter(
                booking_date__gte=now.date(), room=room_id)

            for book_room in booked_rooms:
                if book_room.booking_start_time < now < book_room.booking_end_time:
                    if book_room.meeting is not None and book_room.meeting.meeting_status == 'CO':
                        break
                    time_ago = timeago.format(book_room.booking_end_time, now)
                    message = 'A meeting is ongoing. The room will be available {0}'.format(
                        time_ago)
                    return Response({'Message': message}, status=status.HTTP_400_BAD_REQUEST)

                diff = book_room.booking_start_time - now
                diff_in_minutes = int(diff.seconds/60)

                if diff_in_minutes <= 5:
                    time_ago = timeago.format(now, book_room.booking_start_time)
                    message = 'A meeting will be held {0}'.format(
                        diff_in_minutes)
                    return Response({'Message': message}, status=status.HTTP_400_BAD_REQUEST)

                if book_room.booking_start_time <= new_booking_end_time <= book_room.booking_end_time:
                    time_ago = time_ago.format(now, book_room.booking_start_time)
                    if 'in' in time_ago:
                        time_ago = time_ago.replace('in', 'for')

                    message = 'The duration of {0} is too long. The room is avaiable {1} only'.format(
                        diff_in_minutes, time_ago)
                    return Response({'Message': message}, status=status.HTTP_400_BAD_REQUEST)

            RoomBooking.objects.create(room=room, booked_by=user, meeting=None, booking_date=now.date(
            ), booking_start_time=now, booking_end_time=new_booking_end_time)

            if participants:
                print(participants)
                #check valid participants and send notification

            return Response({'Message': 'Success'}, status=status.HTTP_200_OK)
        except KeyError:
            return Response({'Message': 'duration is required'}, status=status.HTTP_400_BAD_REQUEST)
        # except ValueError:
        #     return Response({'Message': 'duration or room_id is not valid'}, status=status.HTTP_400_BAD_REQUEST)
        except ObjectDoesNotExist:
            return Response({'Message': 'room does not exist'}, status=status.HTTP_400_BAD_REQUEST)
