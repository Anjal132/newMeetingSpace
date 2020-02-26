import datetime

from django.core.exceptions import ObjectDoesNotExist, ValidationError
from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from meeting.utils import meetings_details, root_suggestion
from notifications.models import Notification
from permission.permissions import IsEmployee
from userProfile.models import UserProfile
from utils.otherUtils import send_meeting_mail
from utils.utils import get_user

from .models import Details, Host, Status
from .serializers import DetailsSerializer, MeetingHostSerializer, HostSerializer


'''
If time permits rewrite this view. A lot of repeated code.
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
        print('Create{0}'.format(request.data))
        user = get_user(request)
        room = request.data.pop('room', None)

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)

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
        except TypeError:
            return Response({'Message': 'Invalid query parameters'}, status=status.HTTP_400_BAD_REQUEST)

        suggestions = root_suggestion(meeting_id, room_id)

        if suggestions:
            return Response({'Message': 'Success', 'meeting': meeting_id, 'suggestions': suggestions}, status=status.HTTP_200_OK)
        return Response(status=status.HTTP_204_NO_CONTENT)

    def get_serializer_context(self):
        user = get_user(self.request)
        return {'host': user}




'''
Repeated code. same as sending put request in HostPostponeFinalizeMeetingAPIView
Not removed because android is currently using this. Remove when/if android cooperates.
'''
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
        except Exception:
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
            'type': meeting.type,
        }

        participants = []

        meeting_status = Status.objects.filter(meeting_host=meeting)

        for meet in meeting_status:
            print(meet.participant)
            try:
                participant_profile = UserProfile.objects.get(
                    user=meet.participant)
            except ObjectDoesNotExist:
                continue

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


'''
Participant postpone meeting flow
'''
class AcceptMeetingAPIView(APIView):
    permission_classes = [IsAuthenticated, IsEmployee]

    def post(self, request, *args, **kwargs):
        user = get_user(request)

        try:
            meeting_uid = request.data['meeting_id']
            meeting = Host.objects.get(uid=meeting_uid)
            meeting_details = Details.objects.get(meeting=meeting)
            profile = UserProfile.objects.get(user=user)

            user_participant = Status.objects.filter(meeting_host=meeting_uid, participant=user)
            participants = Status.objects.filter(meeting_host=meeting_uid)

            if not user_participant.exists():
                return Response({'Message': 'Access Forbidden'}, status=status.HTTP_403_FORBIDDEN)
            
            if meeting.meeting_status in ['CO', 'CA', 'PO', 'DR']:
                return Response({'Message': 'Meeting cannot be accepted'}, status=status.HTTP_412_PRECONDITION_FAILED)

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
        except ObjectDoesNotExist:
            return Response({'Message': 'Invalid Meeting ID'}, status=status.HTTP_400_BAD_REQUEST)
        except KeyError:
            return Response({'Message': 'Meeting ID required in body'}, status=status.HTTP_400_BAD_REQUEST)

        return Response({'Message': 'Success'}, status=status.HTTP_200_OK)


'''
Participant postpone meeting flow
'''
class PostponeMeetingAPIView(APIView):
    permission_classes = [IsAuthenticated, IsEmployee]

    def post(self, request, *args, **kwargs):
        try:
            user = get_user(request)
            meeting_uid = request.data['meeting_id']

            meeting = Host.objects.get(uid=meeting_uid)
            meeting_details = Details.objects.get(meeting=meeting)
            profile = UserProfile.objects.get(user=user)

            participants = Status.objects.filter(meeting_host=meeting_uid, participant=user)

            if not participants.exists():
                return Response({'Message': 'Access Forbidden'}, status=status.HTTP_403_FORBIDDEN)
            
            if meeting.type == 'CF':
                return Response({'Message': 'Conferences cannot be postponed'}, status=status.HTTP_412_PRECONDITION_FAILED)

            if meeting.meeting_status in ['CO', 'CA', 'PO', 'DR', 'FI']:
                return Response({'Message': 'This meeting cannot be postponed'}, status=status.HTTP_412_PRECONDITION_FAILED)

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
        except KeyError:
            return Response({'Message': 'Meeting ID required in body'}, status=status.HTTP_400_BAD_REQUEST)
        except ObjectDoesNotExist:
            return Response({'Message': 'Meeting ID is invalid'}, status=status.HTTP_400_BAD_REQUEST)


class DeclineMeetingAPIView(APIView):
    permission_classes = [IsAuthenticated, IsEmployee]

    def post(self, request, *args, **kwargs):
        try:
            user = get_user(request)
            meeting_uid = request.data['meeting_id']

            meeting = Host.objects.get(uid=meeting_uid)
            meeting_details = Details.objects.get(meeting=meeting)
            profile = UserProfile.objects.get(user=user)


            user_participant = Status.objects.filter(meeting_host=meeting_uid, participant=user)
            participants = Status.objects.filter(
                meeting_host=meeting_uid)

            if not user_participant.exists():
                return Response({'Message': 'Access Forbidden'}, status=status.HTTP_403_FORBIDDEN)
            
            if meeting.meeting_status in ['CO', 'CA', 'PO', 'DR']:
                return Response({'Message': 'This meeting cannot be declined'}, status=status.HTTP_412_PRECONDITION_FAILED)

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
        except KeyError:
            return Response({'Message': 'Meeting ID required in body'}, status=status.HTTP_400_BAD_REQUEST)
        except ObjectDoesNotExist:
            return Response({'Message': 'Meeting ID is invalid'}, status=status.HTTP_400_BAD_REQUEST)



'''
When a meeting has been finalized. Send notification to the users.
'''


class HostFinalizeMeetingAPIView(APIView):
    permission_classes = [IsAuthenticated, IsEmployee]

    def post(self, request, *args, **kwargs):
        user = get_user(request)

        try:
            meeting_uid = request.data['meeting_id']
            meeting_status = request.data['status']

            meeting = Host.objects.get(uid=meeting_uid)

            if not user == meeting.host:
                return Response({'Message': 'Access Forbidden'}, status=status.HTTP_403_FORBIDDEN)

            meeting.meeting_status = meeting_status
            meeting.save()

            meeting_details = Details.objects.get(meeting=meeting)
            title = 'Meeting Finalized'
            message = 'Meeting ' + meeting.title + \
                ' has been finalized. Please respond to your invitation if you have not done so already.'
            notification_type = 'meeting'

            participants = Status.objects.filter(meeting_host=meeting)

            for participant in participants:
                if not participant.participant_status in ['DE']:
                    notification = Notification(
                        title=title, message=message, notification_type=notification_type, meeting=meeting_details, user=participant.participant)
                    notification.save()

            return Response({'Message': 'Success'}, status=status.HTTP_200_OK)
        except:
            return Response({'Message': 'Meeting ID, Status required'}, status=status.HTTP_400_BAD_REQUEST)


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
            user_profile = UserProfile.objects.get(user=participant)
            participant_list = {
                'id': participant,
                'name': user_profile.get_full_name,
            }
            participants_list.append(participant_list)
        
        serializer_dict['participant'] = participants_list
        return Response({'Meeting': serializer_dict}, status=status.HTTP_200_OK)


    def update(self, request, *args, **kwargs):
        user = get_user(request)

        try:
            print('Update Meeting:{0}'.format(request.data))
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
        print('Update{0}'.format(request.data))
        user = get_user(request)
        meeting_id = self.kwargs.pop('meeting', None)
        partial = self.kwargs.pop('partial', False)

        if meeting_id is None:
            return Response({'Message': 'Meeting ID required in the URL'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            meeting = Host.objects.get(uid=meeting_id)

            if not meeting.host == user:
                return Response({'Message': 'Access Forbidden'}, status=status.HTTP_403_FORBIDDEN)

            if meeting.meeting_status in ['CO', 'FI', 'CA']:
                return Response({'Message': 'This meeting cannot be postponed.'}, status=status.HTTP_412_PRECONDITION_FAILED)

            # if meeting.type == 'CF':
            #     return Response({'Message': 'Conferences cannot be postponed'}, status=status.HTTP_400_BAD_REQUEST)

            first_instance = Details.objects.filter(meeting=meeting)

            if first_instance.exists():
                serializer = self.get_serializer(
                    first_instance[0], data=request.data, partial=partial)
                serializer.is_valid(raise_exception=True)
                self.perform_update(serializer)
            else:
                serializer = self.get_serializer(data=request.data)
                serializer.is_valid(raise_exception=True)
                self.perform_update(serializer)

            instance = Details.objects.get(meeting=meeting)

            participants = Status.objects.filter(meeting_host=meeting)
            title = 'Meeting has been posponed'
            message = 'The meeting ' + meeting.title + ' has been postponed to ' + instance.meeting_date.isoformat()
            notification_type = 'meeting'

            if first_instance.exists():
                for participant in participants:
                    notification = Notification(user=participant.participant, meeting=instance,
                                                title=title, message=message, notification_type=notification_type)
                    notification.save()

            send_meeting_mail(meeting.participant_email, meeting, instance)

            return Response({'Message': 'Success'}, status=status.HTTP_200_OK)
        except ObjectDoesNotExist:
            return Response({'Message': 'Invalid Meeting ID'}, status=status.HTTP_400_BAD_REQUEST)


'''
{"agenda":"Annual progress from each and every department members.",
"start_date":"2020-02-25",
"title":"Annual Meetup",
"duration":10800,
"type":"PU",
"end_date":"2020-02-28",
"meeting_to_participant":[{"participant":"4"},{"participant":"6"}], "timezone":"Asia/Kathmandu", "room":"current"}
'''
