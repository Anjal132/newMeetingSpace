import datetime

from django.core.exceptions import ValidationError
from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from meeting.utils import (generate_suggestions, get_app_events,
                           get_events_from_google_calendar,
                           get_single_events_dict, meetings_details)
from notifications.models import Notification
from permission.permissions import IsEmployee
from userProfile.models import UserProfile
from utils.utils import get_user

from .models import Details, Host, Status
from .serializers import DetailsSerializer, MeetingHostSerializer


'''
If time permits rewrite accept decline and postpone code. A lot of repeated code.
'''


class MeetingOnDateAPIView(APIView):
    permission_classes = [IsAuthenticated, IsEmployee]

    def get(self, request, *args, **kwargs):
        date = request.query_params.get('date', None)

        if date is None:
            return Response({'Message': 'Invalid query parameters'}, status=status.HTTP_400_BAD_REQUEST)

        user = get_user(request)

        try:
            meetings_on_date = Details.objects.filter(meeting_date=date)
        except ValidationError:
            return Response({'Message': 'Invalid date format'}, status=status.HTTP_400_BAD_REQUEST)
        meetings = []

        for meeting_on_date in meetings_on_date:
            participant = Status.objects.filter(
                meeting_host=meeting_on_date.meeting).filter(participant=user)

            if not meeting_on_date.meeting.host == user:
                if not participant.exists():
                    continue

            meeting_on_day = {
                'title': meeting_on_date.meeting.title,
                'status': meeting_on_date.meeting.meeting_status,
                'start_time': meeting_on_date.start_time,
                'end_time': meeting_on_date.end_time,
                'host': meeting_on_date.meeting.host == user,
                'room': meeting_on_date.room.room_number
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
        try:
            print(request.data)
            user = get_user(request)
            room = request.data['room']

            serializer = self.get_serializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            self.perform_create(serializer)

            meeting_id = serializer.data['uid']
            google_events = get_events_from_google_calendar(meeting_id)

            app_events = get_app_events(meeting_id)
            events = get_single_events_dict(google_events, app_events)
            room_id = -1

            try:
                room_id = int(room)
                profiles = UserProfile.objects.filter(room=room_id)

                if profiles.exists():
                    own_room = False

                    for profile in profiles:
                        if profile.user == user:
                            own_room = True

                    if not own_room:
                        return Response({'Message': 'Cannot host meeting in private office of another employee.'}, status=status.HTTP_400_BAD_REQUEST)

            except ValueError:
                if room == 'current':
                    profile = UserProfile.objects.get(user=user)
                    if profile.room is None:
                        return Response({'Message': 'Please update your profile to host meeting in your room.'}, status=status.HTTP_400_BAD_REQUEST)
                    room_id = profile.room.id
                elif room == 'suggestion':
                    room_id = -1
                else:
                    return Response({'Message': 'Invalid query parameters'}, status=status.HTTP_400_BAD_REQUEST)

            suggestions = generate_suggestions(events, meeting_id, room_id)

            if suggestions:
                return Response({'Message': 'Success', 'meeting': meeting_id, 'suggestions': suggestions}, status=status.HTTP_200_OK)
            return Response(status=status.HTTP_204_NO_CONTENT)
        except:
            return Response({'Message': 'Suggestions could not be generated. Please change the parameters and try again.'}, status=status.HTTP_400_BAD_REQUEST)

    def get_serializer_context(self):
        user = get_user(self.request)
        return {'host': user}


class MeetingFinalizeAPIView(generics.CreateAPIView):
    permission_classes = [IsAuthenticated, IsEmployee]
    queryset = Details.objects.all()
    serializer_class = DetailsSerializer

    def create(self, request, *args, **kwargs):
        print(request.data)
        try:
            serializer = self.get_serializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            self.perform_create(serializer)
            return Response({'Message': 'Success'}, status=200)
        except:
            print(serializer.errors)
            return Response({'Message': 'Host meeting failed. Please try again.', 'Errors': serializer.errors}, status=400)


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

        meetings = Details.objects.filter(
            meeting_date__lte=datetime.date.today()).order_by('-meeting_date', '-start_time')

        if upcoming_query_param:
            meetings = Details.objects.filter(
                meeting_date__gte=datetime.date.today()).order_by('meeting_date', 'start_time')

        if not meetings.exists():
            return Response(status=status.HTTP_204_NO_CONTENT)

        response_message = meetings_details(
            meetings, meetings_query_param, user, upcoming_query_param)

        if response_message:
            return Response({'Upcoming Meetings': response_message}, status=status.HTTP_200_OK)
        return Response(status=status.HTTP_204_NO_CONTENT)

    def post(self, request, *args, **kwargs):
        # handle error for when user is logged in but is neither host nor participant
        # can do it by checking if user is in host and status table for the particular meeting
        user = get_user(request)

        if 'id' in request.data:
            notif_id = request.data['id']
            notification = Notification.objects.get(id=notif_id)
            meeting_detail = Details.objects.get(id=notification.meeting_id)
            meeting = Host.objects.get(uid=meeting_detail.meeting.uid)

        elif 'meeting_id' in request.data:
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
            'start_time': meeting_detail.start_time.strftime('%I:%M%p'),
            'end_time': meeting_detail.end_time.strftime('%I:%M%p'),
            'room': meeting_detail.room.room_number,
            'meetingId': meeting.uid,
        }

        participants = []

        meeting_status = Status.objects.filter(meeting_host=meeting)

        for meet in meeting_status:
            participant_profile = UserProfile.objects.get(
                user=meet.participant)

            if (user == meeting.host):
                participant = {
                    'name': participant_profile.get_full_name,
                    'status': meet.participant_status,
                    'message': meet.participant_message
                }
            else:
                participant = {
                    'name': participant_profile.get_full_name,
                    'status': meet.participant_status,
                }

            participants.append(participant)

        response['participants'] = participants

        return Response(response, status=status.HTTP_200_OK)


class AcceptMeetingAPIView(APIView):
    permission_classes = [IsAuthenticated, IsEmployee]

    def post(self, request, *args, **kwargs):
        user = get_user(request)
        meeting_uid = request.data['meeting_id']

        meeting = Host.objects.get(uid=meeting_uid)
        meeting_details = Details.objects.get(meeting=meeting)
        profile = UserProfile.objects.get(user=user)

        participants = Status.objects.filter(
            meeting_host=meeting_uid)

        participant_status = True

        for participant in participants:
            if participant.participant == user:
                participant.participant_status = 'AC'
                participant.save()

            if participant.participant_status == 'PE' or participant.participant_status == 'PO':
                participant_status = False

        if participant_status:
            meeting = Host.objects.get(uid=meeting_uid)
            meeting.meeting_status = 'FI'
            meeting.save()

        title = 'Invitation Accepted'

        message = profile.get_full_name + \
            ' has accepted your invitation to meeting ' + meeting.title + '.'
        notification_type = 'meeting'
        notification = Notification(
            title=title, message=message, notification_type=notification_type, meeting=meeting_details, user=meeting.host)
        notification.save()

        return Response({'Message': 'Success'}, status=status.HTTP_200_OK)


class PostponeMeetingAPIView(APIView):
    permission_classes = [IsAuthenticated, IsEmployee]

    def post(self, request, *args, **kwargs):
        user = get_user(request)
        meeting_uid = request.data['meeting_id']

        meeting = Host.objects.get(uid=meeting_uid)
        meeting_details = Details.objects.get(meeting=meeting)
        profile = UserProfile.objects.get(user=user)

        participants = Status.objects.filter(
            meeting_host=meeting_uid)

        meeting = Host.objects.get(uid=meeting_uid)

        if meeting.meeting_status == 'FI':
            return Response({'Message': 'The meeting has already been finalized.'}, status=status.HTTP_200_OK)

        for participant in participants:
            if participant.participant == user:
                participant.participant_status = 'PO'
                participant.participant_message = request.data['participant_message']
                participant.save()

        title = 'Postponement of meeting requested'

        message = profile.get_full_name + \
            ' has requested to postpone meeting ' + meeting.title + '.'
        notification_type = 'meeting'
        notification = Notification(
            title=title, message=message, notification_type=notification_type, meeting=meeting_details, user=meeting.host)
        notification.save()

        return Response({'Message': 'Success'}, status=status.HTTP_200_OK)


class DeclineMeetingAPIView(APIView):
    permission_classes = [IsAuthenticated, IsEmployee]

    def post(self, request, *args, **kwargs):
        user = get_user(request)
        meeting_uid = request.data['meeting_id']

        meeting = Host.objects.get(uid=meeting_uid)
        meeting_details = Details.objects.get(meeting=meeting)
        profile = UserProfile.objects.get(user=user)

        participants = Status.objects.filter(
            meeting_host=meeting_uid)

        participant_status = True

        for participant in participants:
            if participant.participant == user:
                participant.participant_status = 'DE'
                participant.participant_message = request.data['participant_message']
                participant.save()

            if participant.participant_status == 'PE' or participant.participant_status == 'PO':
                participant_status = False

        if participant_status:
            meeting = Host.objects.get(uid=meeting_uid)
            meeting.meeting_status = 'FI'
            meeting.save()

        title = 'Invitation Declined'

        message = profile.get_full_name + \
            ' has declined your invitation to meeting ' + meeting.title + '.'
        notification_type = 'meeting'
        notification = Notification(
            title=title, message=message, notification_type=notification_type, meeting=meeting_details, user=meeting.host)
        notification.save()

        return Response({'Message': 'Success'}, status=status.HTTP_200_OK)


class HostFinalizeMeetingAPIView(APIView):
    permission_classes = [IsAuthenticated, IsEmployee]

    def post(self, request, *args, **kwargs):
        user = get_user(request)

        try:
            meeting_uid = request.data['meeting_id']
            meeting_status = request.data['status']

            meeting = Host.objects.get(uid=meeting_uid)

            if not user == meeting.host:
                return Response({'Message': 'Forbidden Access'}, status=status.HTTP_403_FORBIDDEN)

            meeting.meeting_status = meeting_status
            meeting.save()
            return Response({'Message': 'Success'}, status=status.HTTP_202_ACCEPTED)
        except:
            return Response({'Message': 'Meeting ID, Status required'}, status=status.HTTP_400_BAD_REQUEST)
