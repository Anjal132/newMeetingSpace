import pytz, datetime
from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from rest_framework import filters, status
from rest_framework.generics import ListAPIView, RetrieveUpdateAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from permission.permissions import IsCompanyAdmin, IsEmployee
from userProfile.models import UserProfile
from users.models import User
from users.serializers import (ProfileSearchSerializer,
                               ProfileSerializer)
from users.v1.apiSerializers import (ActiveInactiveUserSerializer,
                                     UserListSerializer)
from utils.utils import get_user
from notifications.models import FCMRegistrationToken


# class AddBatchEmployeeAPIView(APIView):
#     authentication_classes = ()
#     permission_classes = ()

#     '''
#     from django.db import connection
#     import requests
#     schema_name = ''
#     url = 'http://localhost:8000/auth/v1/add_batch_users'
#     connection.set_schema(schema_name=schema_name)
#     files = {'file': open('/home/ojha/file.csv', 'rb')}
#     values = {'building':2, 'department':2}
#     r = requests.post(url)
#     '''

#     def post(self, request):
#         print(request.headers)
#         print(request.data)

#         serializer = BatchUploadSerializer(data=request.data)

#         if(serializer.is_valid()):
#             print(serializer.validated_data)
#             file = serializer.validated_data['file']

#             filename = settings.BASE_DIR + '/csv/' + \
#                 str(datetime.timestamp(datetime.now())) + file.name
#             with open(filename, 'wb+') as destination:
#                 for chunk in file.chunks():
#                     destination.write(chunk)

#             add_batch_users.delay(filename)
#             return Response({'Message': 'Successfully uploaded. Please refresh the page to see changes.'}, status=200)
#         return Response({'Message': serializer.errors}, status=400)


class UserDetailAPIView(RetrieveUpdateAPIView):
    permission_classes = (IsAuthenticated, IsCompanyAdmin)
    serializer_class = ActiveInactiveUserSerializer

    def get_queryset(self):
        user = get_user(self.request)
        schema_name = self.request.headers['X_DTS_SCHEMA']
        return User.objects.filter(temp_name=schema_name).exclude(id=user.id)


class GetSuggestionsAPIView(ListAPIView):
    '''
    Function for search as you type. May replace with Web Sockets
    '''

    permission_classes = (IsAuthenticated, IsEmployee)

    serializer_class = ProfileSearchSerializer
    filter_backends = [filters.SearchFilter]
    search_fields = ['^first_name', '^middle_name', '^last_name']

    def get_queryset(self):
        search = self.request.query_params.get('search', None)

        if search is None or search == '':
            return UserProfile.objects.none()

        user = get_user(self.request)

        users_in_same_company = list(UserProfile.objects.all().values_list('user_id', flat=True))
        users_in_same_company.remove(user.id)

        active_users = list(User.objects.filter(
            id__in=users_in_same_company).exclude(is_verified=False, is_active=False).values_list('id', flat=True))
        return UserProfile.objects.filter(user_id__in=active_users)


class GetProfileAPIView(APIView):
    permission_classes = (IsAuthenticated, IsEmployee)

    '''
    Method to update profile for users
    '''

    def put(self, request):
        print(request.data)
        user = get_user(request)
        try:
            request.data._mutable = True
            request.data['user'] = user.id
            request.data._mutable = False
        except AttributeError:
            request.data['user'] = user.id

        try:
            instance = UserProfile.objects.get(user=user)
        except ObjectDoesNotExist:
            return Response({'Message': 'Profile not found'}, status=status.HTTP_400_BAD_REQUEST)

        serializer = ProfileSerializer(instance=instance, data=request.data)

        if serializer.is_valid():
            validated_data = serializer.validated_data
            building = validated_data.pop('building', None)

            office_start_time = validated_data.pop('office_start_time', None)
            office_end_time = validated_data.pop('office_end_time', None)
            timezone = validated_data.pop('timezone', None)

            if office_start_time is not None or office_end_time is not None:
                if office_start_time is None or office_end_time is None or timezone is None:
                    return Response({'Message': 'Office start time, office end time and timezone are all required'}, status=status.HTTP_400_BAD_REQUEST)
                
                now = datetime.datetime.now(tz=pytz.timezone(timezone))
                
                office_start_time = now.replace(hour=office_start_time.hour, minute=office_start_time.minute, second=0, microsecond=0)
                office_end_time = now.replace(hour=office_end_time.hour, minute=office_end_time.minute, second=0, microsecond=0)

                validated_data['office_start_time'] = office_start_time.astimezone(pytz.UTC).time()
                validated_data['office_end_time'] = office_end_time.astimezone(pytz.UTC).time()

            if building is None and instance.building is None:
                if 'room' in validated_data or 'floor' in validated_data:
                    return Response({'Message': 'Cannot add room without building'}, status=status.HTTP_400_BAD_REQUEST)

            if building is not None or instance.building is not None:
                if building is None:
                    building = instance.building
                elif building.is_available == 'SD':
                    return Response({'Message': 'The building has already been shut down'}, status=status.HTTP_400_BAD_REQUEST)

                if 'room' in validated_data:
                    room = validated_data['room']

                    if building.id != room.property.id:
                        return Response({'Message': 'Room does not exist on the building'}, status=status.HTTP_400_BAD_REQUEST)

                    if room.room_type != 'PO':
                        return Response({'Message': 'Room is not a private office'}, status=status.HTTP_400_BAD_REQUEST)

                    if not room.is_active:
                        return Response({'Message': 'Room is not active'}, status=status.HTTP_400_BAD_REQUEST)

                validated_data['building'] = building

            serializer.save()
            serializer_dict = serializer.data
            serializer_dict['profile_set'] = True
            serializer_dict['workplace_set'] = True

            if instance.get_full_name is None:
                serializer_dict['profile_set'] = False

            if instance.building is None:
                serializer_dict['workplace_set'] = False

            serializer_dict['message'] = 'Profile successfully updated'
            serializer_dict.pop('id')
            serializer_dict.pop('user')

            return Response(serializer_dict, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class GetUsersAPIView(ListAPIView):
    permission_classes = (IsAuthenticated, IsCompanyAdmin)
    serializer_class = UserListSerializer
    queryset = User.objects.all()

    def get_queryset(self):
        user = get_user(self.request)
        schema_name = user.temp_name
        return User.objects.filter(temp_name=schema_name).exclude(id=user.id)


class LogoutAPIView(APIView):
    permission_classes = (IsAuthenticated, IsEmployee)

    def get(self, request, *args, **kwargs):
        user = get_user(request)

        FCMRegistrationToken.objects.filter(user=user).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
