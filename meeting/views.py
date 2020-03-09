import datetime

import pytz
from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist, ValidationError
from pytz.exceptions import UnknownTimeZoneError
from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from meeting.utils import (is_meeting_valid, is_participant, meetings_details,
                           root_suggestion)
from permission.permissions import IsEmployee
from property.models import RoomBooking
from userProfile.models import UserProfile
from utils.otherUtils import send_meeting_mail
from utils.utils import get_user

from .models import Details, Host, Status
from .serializers import (DetailsSerializer, HostSerializer,
                          MeetingHostSerializer)


class MeetingOnDateAPIView(APIView):
    permission_classes = [IsAuthenticated, IsEmployee]

    def get(self, request, *args, **kwargs):
        start_date = request.query_params.get('start_date', None)
        end_date = request.query_params.get('end_date', None)

        if start_date is None:
            return Response({'Message': 'Invalid query parameters'}, status=status.HTTP_400_BAD_REQUEST)

        if end_date is None:
            end_date = start_date

        user = get_user(request)

        try:
            meetings_on_date = Details.objects.filter(
                meeting_date__gte=start_date, meeting_date__lte=end_date)
        except ValidationError:
            return Response({'Message': 'Invalid date format'}, status=status.HTTP_400_BAD_REQUEST)
        meetings = []

        for meeting_on_date in meetings_on_date:
            if not meeting_on_date.meeting.host == user:
                if not is_participant(meeting_on_date.meeting.uid, user):
                    continue

            meeting_on_day = {
                'title': meeting_on_date.meeting.title,
                'status': meeting_on_date.meeting.meeting_status,
                'start_time': meeting_on_date.start_time.strftime('%I:%M %p'),
                'end_time': meeting_on_date.end_time.strftime('%I:%M %p'),
                'host': meeting_on_date.meeting.host == user,
                'room': meeting_on_date.room.room_number,
                'meeting_date': meeting_on_date.meeting_date
            }

            meetings.append(meeting_on_day)

        if meetings:
            return Response({'Meetings': meetings}, status=status.HTTP_200_OK)
        return Response(status=status.HTTP_204_NO_CONTENT)


class HostMeetingView(generics.CreateAPIView):
    permission_classes = [IsAuthenticated, IsEmployee]
    queryset = Host.objects.all()
    serializer_class = MeetingHostSerializer

    def create(self, request, *args, **kwargs):
        print(request.data)
        user = get_user(request)
        user_profile = UserProfile.objects.get(user=user)
        if user_profile.building is None:
            return Response({'Message': 'Please add building to your workplace before hosting a meeting'}, status=status.HTTP_412_PRECONDITION_FAILED)

        try:
            room = request.data['room']
        except KeyError:
            print(1)
            return Response({'Message': 'Room parameter not sent'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            serializer = self.get_serializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            self.perform_create(serializer)
        except ValidationError as error:
            return Response(error, status=status.HTTP_400_BAD_REQUEST)

        meeting_id = serializer.data['uid']

        try:
            room_id = int(room)
            profiles = UserProfile.objects.filter(room=room_id)

            if profiles.exists():
                own_room = False

                for profile in profiles:
                    if profile.user == user:
                        own_room = True

                if not own_room:
                    print(2)
                    return Response({'Message': 'Cannot host meeting in private office of another employee.'}, status=status.HTTP_400_BAD_REQUEST)

        except ValueError:
            if room == 'current':
                profile = UserProfile.objects.get(user=user)
                if profile.room is None:
                    print(3)
                    return Response({'Message': 'Please update your profile to host meeting in your room.'}, status=status.HTTP_400_BAD_REQUEST)
                room_id = profile.room.id
            elif room == 'suggestion':
                room_id = -1
            else:
                print(4)
                return Response({'Message': 'Invalid room parameter'}, status=status.HTTP_400_BAD_REQUEST)
        except TypeError:
            print(5)
            return Response({'Message': 'Room parameter not sent'}, status=status.HTTP_400_BAD_REQUEST)

        suggestions = root_suggestion(meeting_id, room_id)

        meeting = Host.objects.get(uid=meeting_id)
        meeting_participants = Status.objects.filter(meeting_host=meeting)

        participants = []

        for meeting_participant in meeting_participants:
            participant_profile = UserProfile.objects.get(
                user=meeting_participant.participant)
            profile_pic = ''

            if participant_profile.profile_pics != '':
                profile_pic = settings.MEDIA_URL + \
                    str(participant_profile.profile_pics)

            participant = {
                'name': participant_profile.get_full_name,
                'profile_pics': profile_pic,
            }
            participants.append(participant)

        if suggestions:
            return Response({
                'Message': 'Success',
                'meeting': meeting_id,
                'suggestions': suggestions,
                'participants_via_email': meeting.participant_email,
                'participants': participants
            }, status=status.HTTP_200_OK)
        return Response(status=status.HTTP_204_NO_CONTENT)

    def get_serializer_context(self):
        user = get_user(self.request)
        return {'host': user}


class UpcomingMeetingsAPIView(APIView):
    permission_classes = [IsAuthenticated, IsEmployee]

    def get(self, request, *args, **kwargs):
        meetings_query_param = request.query_params.get('meetings', None)
        upcoming_query_param = request.query_params.get('upcoming', None)

        if meetings_query_param is None or upcoming_query_param is None:
            return Response({'Message': 'Invalid query parameters'}, status=status.HTTP_400_BAD_REQUEST)

        if upcoming_query_param == 'upcoming':
            upcoming_query_param = True
        elif upcoming_query_param == 'previous':
            upcoming_query_param = False
        else:
            return Response({'Message': 'Invalid query parameters'}, status=status.HTTP_400_BAD_REQUEST)

        user = get_user(request)
        now = datetime.datetime.now(pytz.UTC)

        meetings = Details.objects.filter(
            meeting_date__lte=now.date()).order_by('-meeting_date', '-start_time')

        if upcoming_query_param:
            meetings = Details.objects.filter(
                meeting_date__gte=now.date()).order_by('meeting_date', 'start_time')

        if not meetings.exists():
            return Response(status=status.HTTP_204_NO_CONTENT)

        response_message = meetings_details(
            meetings, meetings_query_param, user, upcoming_query_param)

        if response_message:
            return Response({'Upcoming Meetings': response_message}, status=status.HTTP_200_OK)
        return Response(status=status.HTTP_204_NO_CONTENT)

    def post(self, request, *args, **kwargs):
        user = get_user(request)

        try:
            if 'meeting_id' in request.data:
                meeting_uid = request.data['meeting_id']
                meeting_detail = Details.objects.get(meeting_id=meeting_uid)
                meeting = Host.objects.get(uid=meeting_uid)

            profile = UserProfile.objects.get(user=meeting.host)

            response = {
                'title': meeting.title,
                'agenda': meeting.agenda,
                'hosted_by': profile.get_full_name,
                'host': user == meeting.host,
                'status': meeting.meeting_status,
                'participants_email': meeting.participant_email,
                'date': meeting_detail.meeting_date,
                'start_time': meeting_detail.start_time.strftime('%I:%M %p'),
                'end_time': meeting_detail.end_time.strftime('%I:%M %p'),
                'room': meeting_detail.room.room_number,
                'meetingId': meeting.uid,
                'type': meeting.type,
                'building': meeting_detail.room.property.name
            }

            participants = []

            meeting_status = Status.objects.filter(meeting_host=meeting)

            for meet in meeting_status:
                try:
                    participant_profile = UserProfile.objects.get(
                        user=meet.participant)
                except ObjectDoesNotExist:
                    continue

                profile_pic = ''
                if participant_profile.profile_pics != '':
                    profile_pic = settings.MEDIA_URL + \
                        str(participant_profile.profile_pics)

                if (user == meeting.host):
                    participant = {
                        'name': participant_profile.get_full_name,
                        'status': meet.participant_status,
                        'message': meet.participant_message,
                        'profile_pics': profile_pic
                    }
                else:
                    participant = {
                        'name': participant_profile.get_full_name,
                        'status': meet.participant_status,
                        'profile_pics': profile_pic
                    }

                participants.append(participant)

            response['participants'] = participants
        except KeyError:
            return Response({'Message': 'meeting_id not found'}, status=status.HTTP_400_BAD_REQUEST)
        except ObjectDoesNotExist:
            return Response({'Message': 'Meeting with the meeting_id not found'}, status=status.HTTP_400_BAD_REQUEST)
        except ValidationError:
            return Response({'Message': 'Invalid uid'}, status=status.HTTP_400_BAD_REQUEST)

        return Response(response, status=status.HTTP_200_OK)


class ChangeParticipantStatusAPIView(APIView):
    permission_classes = [IsAuthenticated, IsEmployee]

    def post(self, request, *args, **kwargs):
        user = get_user(request)

        try:
            meeting_id = request.data['meeting_id']
            change_status_to = request.data['participant_status']

            try:
                participant_message = request.data['participant_message']
            except KeyError:
                participant_message = None

            meeting = Host.objects.get(uid=meeting_id)

            if not is_participant(meeting_id, user):
                return Response({'Message': 'Access Forbidden'}, status=status.HTTP_403_FORBIDDEN)

            all_participant_status = ['AC', 'DE', 'PO']
            if change_status_to not in all_participant_status:
                return Response({'Message': 'Invalid participant_status'}, status=status.HTTP_400_BAD_REQUEST)

            invalid_meeting_param = ['CA', 'CO', 'DR', 'ON', 'FI']

            if change_status_to != 'PO':
                invalid_meeting_param = ['CA', 'CO', 'DR', 'ON']

            message, invalid_meeting = is_meeting_valid(
                meeting, invalid_meeting_param)

            if meeting.type == 'CF' and change_status_to == 'PO':
                return Response({'Message': 'Conferences cannot be postponed'}, status=status.HTTP_412_PRECONDITION_FAILED)

            if invalid_meeting:
                return Response({'Message': message}, status=status.HTTP_412_PRECONDITION_FAILED)

            participant = Status.objects.get(
                meeting_host=meeting_id, participant=user)

            if participant.participant_status == change_status_to:
                return Response(status=status.HTTP_204_NO_CONTENT)

            participant.participant_status = change_status_to

            if participant_message is not None:
                participant.participant_message = participant_message

            participant.save()
        except ValidationError as error:
            print(error)
            return Response({'Message': 'meeting_id is not a valid UID'}, status=status.HTTP_400_BAD_REQUEST)
        except ObjectDoesNotExist:
            return Response({'Message': 'Meeting not found'}, status=status.HTTP_400_BAD_REQUEST)
        except KeyError:
            return Response({'Message': 'meeting_id and change_status_to cannot be blank'}, status=status.HTTP_400_BAD_REQUEST)

        return Response({'Message': 'Success'}, status=status.HTTP_200_OK)


class ChangeHostStatusAPIView(APIView):
    def post(self, request, *args, **kwargs):
        print(request.data)
        user = get_user(request)
        message = 'Success'
        try:
            meeting_id = request.data['meeting_id']
            change_status_to = request.data['meeting_status']

            meeting = Host.objects.get(uid=meeting_id)
            meeting_detail = Details.objects.get(meeting=meeting_id)

            now = datetime.datetime.now(pytz.UTC)
            meeting_datetime = datetime.datetime.combine(
                meeting_detail.meeting_date, meeting_detail.end_time, tzinfo=pytz.UTC)

            if not meeting.host == user:
                return Response({'Message': 'Access Forbidden'}, status=status.HTTP_403_FORBIDDEN)

            if meeting_datetime < now:
                message = 'Cannot change meeting_status now'
                return Response({'Message': message}, status=status.HTTP_400_BAD_REQUEST)

            if change_status_to not in ['FI', 'CO', 'CA']:
                message = 'Meeting status must be FI, CO or CA'
                return Response({'Message': message}, status=status.HTTP_400_BAD_REQUEST)

            if meeting.meeting_status == 'CA' and change_status_to == 'CO':
                print(1)
                message = 'Cannot change meeting_status now'
                return Response({'Message': message}, status=status.HTTP_400_BAD_REQUEST)

            if not meeting.meeting_status == 'ON' and change_status_to == 'CO':
                print(2)
                message = 'Cannot change meeting_status now'
                return Response({'Message': message}, status=status.HTTP_400_BAD_REQUEST)

            if meeting.meeting_status == change_status_to:
                message = 'meeting_status is already {0}'.format(
                    change_status_to)

            meeting.meeting_status = change_status_to
            meeting.save()
        except KeyError:
            return Response({'Message': 'meeting_id and meeting_status are required'}, status=status.HTTP_400_BAD_REQUEST)
        except ValidationError:
            return Response({'Message': 'meeting_id is not a valid uid'}, status=status.HTTP_400_BAD_REQUEST)
        except ObjectDoesNotExist:
            return Response({'Message': 'Meeting not found.'}, status=status.HTTP_400_BAD_REQUEST)
        return Response({'Message': message}, status=status.HTTP_200_OK)


class HostPostponeMeetingAPIView(generics.RetrieveUpdateAPIView):
    permission_classes = [IsAuthenticated, IsEmployee]
    queryset = Host.objects.all()
    lookup_field = 'uid'

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        serializer_dict = serializer.data
        participants = serializer_dict.pop('participant', None)
        participants_list = []

        for participant in participants:
            profile_pic = ''
            user_profile = UserProfile.objects.get(user=participant)

            if user_profile.profile_pics != '':
                profile_pic = settings.MEDIA_URL + \
                    str(user_profile.profile_pics)

            participant_list = {
                'id': participant,
                'name': user_profile.get_full_name,
                'profile_pics': profile_pic
            }
            participants_list.append(participant_list)

        serializer_dict['participant'] = participants_list
        return Response({'Meeting': serializer_dict}, status=status.HTTP_200_OK)

    def update(self, request, *args, **kwargs):
        user = get_user(request)

        try:
            meeting_id = self.kwargs['uid']
            partial = self.kwargs.pop('partial', False)
            room = request.data.pop('room', None)
            meeting = Host.objects.get(uid=meeting_id)

            if not meeting.host == user:
                return Response({'Message': 'Forbidden Access'}, status=status.HTTP_403_FORBIDDEN)

            if meeting.meeting_status in ['CO', 'FI', 'CA']:
                return Response({'Message': 'This meeting cannot be postponed.'}, status=status.HTTP_412_PRECONDITION_FAILED)

            if room == 'current':
                profile = UserProfile.objects.get(user=user)
                if profile.room is None:
                    return Response({'Message': 'Please update your profile to host meeting in your room.'}, status=status.HTTP_400_BAD_REQUEST)
                room_id = profile.room.id
            elif room == 'suggestion':
                room_id = -1
            else:
                return Response({'Message': 'Invalid query parameters'}, status=status.HTTP_400_BAD_REQUEST)

            instance = Host.objects.get(uid=meeting_id)
            serializer = self.get_serializer(
                instance, data=request.data, partial=partial)
            serializer.is_valid(raise_exception=True)
            self.perform_update(serializer)

            suggestions = root_suggestion(meeting_id, room_id)

            if suggestions:
                return Response({'Message': 'Success', 'meeting': meeting_id, 'suggestions': suggestions}, status=status.HTTP_200_OK)
            return Response(status=status.HTTP_204_NO_CONTENT)
        except KeyError:
            return Response({'Message': 'Meeting ID required in the URL'}, status=status.HTTP_400_BAD_REQUEST)
        except ValidationError:
            return Response({'Message': 'Validation Error. Please refine your values and try again.'}, status=status.HTTP_400_BAD_REQUEST)
        except ObjectDoesNotExist:
            return Response({'Message': 'Invalid Meeting ID'}, status=status.HTTP_400_BAD_REQUEST)

    def get_serializer_context(self):
        user = get_user(self.request)
        return {'host': user}

    def get_serializer_class(self):
        if self.request.method == 'PUT':
            return MeetingHostSerializer

        if self.request.method == 'GET':
            return HostSerializer
        return MeetingHostSerializer


class HostPostponeFinalizeMeetingAPIView(generics.UpdateAPIView):
    permission_classes = (IsAuthenticated, IsEmployee)
    serializer_class = DetailsSerializer
    queryset = Details.objects.all()
    lookup_field = 'meeting'

    def update(self, request, *args, **kwargs):
        print(request.data)
        user = get_user(request)
        meeting_id = self.kwargs.pop('meeting', None)
        partial = self.kwargs.pop('partial', False)

        if 'timezone' not in request.data:
            return Response({'Message': 'Timezone also required'}, status=status.HTTP_400_BAD_REQUEST)

        if meeting_id is None:
            return Response({'Message': 'Meeting ID required in the URL'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            meeting = Host.objects.get(uid=meeting_id)

            if not meeting.host == user:
                return Response({'Message': 'Access Forbidden'}, status=status.HTTP_403_FORBIDDEN)

            if meeting.meeting_status in ['CO', 'FI', 'CA']:
                return Response({'Message': 'This meeting cannot be postponed.'}, status=status.HTTP_412_PRECONDITION_FAILED)

            try:
                timezone = pytz.timezone(request.data['timezone'])
                now = datetime.datetime.now(timezone)
            except UnknownTimeZoneError:
                return Response({'Message': 'Unknown timezone'}, status=status.HTTP_400_BAD_REQUEST)
            except AttributeError:
                return Response({'Message': 'Unknown timezone'}, status=status.HTTP_400_BAD_REQUEST)

            start_time = request.data['meeting_date'] + \
                request.data['start_time']
            end_time = request.data['meeting_date'] + request.data['end_time']
            try:
                meeting_start_time = datetime.datetime.strptime(
                    start_time, '%Y-%m-%d%I:%M %p')
                meeting_start_time = now.replace(meeting_start_time.year, meeting_start_time.month, meeting_start_time.day,
                                                 meeting_start_time.hour, meeting_start_time.minute, meeting_start_time.second,
                                                 meeting_start_time.microsecond)

                meeting_end_time = datetime.datetime.strptime(
                    end_time, '%Y-%m-%d%I:%M %p')
                meeting_end_time = now.replace(meeting_end_time.year, meeting_end_time.month, meeting_end_time.day,
                                               meeting_end_time.hour, meeting_end_time.minute, meeting_end_time.second,
                                               meeting_end_time.microsecond)

            except ValueError:
                return Response({'Message': 'Date required in yyyy-mm-dd format and time required in hh:mm PM format'}, status=status.HTTP_400_BAD_REQUEST)

            meeting_start_time = meeting_start_time.astimezone(pytz.UTC)
            meeting_end_time = meeting_end_time.astimezone(pytz.UTC)
            try:
                _mutable = request.data._mutable
                request.data['meeting_date'] = meeting_start_time.date(
                ).isoformat()
                request.data['start_time'] = meeting_start_time.time(
                ).isoformat()
                request.data['end_time'] = meeting_end_time.time().isoformat()
                request.data._mutable = _mutable

            except AttributeError:
                request.data['meeting_date'] = meeting_start_time.date(
                ).isoformat()
                request.data['start_time'] = meeting_start_time.time(
                ).isoformat()
                request.data['end_time'] = meeting_end_time.time().isoformat()

            first_instance = Details.objects.filter(meeting=meeting)
            try:
                print(request.data)
                if first_instance.exists():
                    serializer = self.get_serializer(
                        first_instance[0], data=request.data, partial=partial)
                    serializer.is_valid(raise_exception=True)
                    self.perform_update(serializer)
                else:
                    serializer = self.get_serializer(data=request.data)
                    serializer.is_valid(raise_exception=True)
                    self.perform_update(serializer)
            except ValidationError:
                return Response(ValidationError, status=status.HTTP_400_BAD_REQUEST)

            instance = Details.objects.get(meeting=meeting)
            send_meeting_mail(meeting.participant_email, meeting, instance)

            try:
                book_room = RoomBooking.objects.get(meeting=meeting)
                book_room.room = instance.room
                book_room.booking_start_time = meeting_start_time
                book_room.booking_end_time = meeting_end_time
                book_room.save()
            except ObjectDoesNotExist:
                RoomBooking.objects.create(room=instance.room, booked_by=meeting.host, meeting=meeting, booking_date=meeting_start_time.date(), booking_start_time=meeting_start_time,
                                    booking_end_time=meeting_end_time)
            return Response({'Message': 'Success'}, status=status.HTTP_200_OK)
        except ObjectDoesNotExist:
            return Response({'Message': 'Invalid Meeting ID'}, status=status.HTTP_400_BAD_REQUEST)
