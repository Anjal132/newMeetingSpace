import json

import requests
from rest_framework import status
from rest_framework.generics import ListAPIView, UpdateAPIView, CreateAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from notifications.models import Notification, FCMRegistrationToken
from notifications.serializers import (NotificationReadSerializer,
                                       NotificationSerializer, FCMTokenSerializer)
from permission.permissions import IsEmployee
from utils.utils import get_user

from .utils import get_access_token

# Create your views here.

class NotificationReadAPIView(APIView):
    permission_classes = [IsAuthenticated, IsEmployee]

    def get(self, request, *args, **kwargs):
        user = get_user(request)
        unread = Notification.objects.filter(user=user).filter(read=False).count()

        return Response({'Unread': unread}, status=status.HTTP_200_OK)


class AllNotificationsAPIView(ListAPIView):
    permission_classes = [IsAuthenticated, IsEmployee,]
    serializer_class = NotificationSerializer
    
    def get_queryset(self):
        user = get_user(self.request)

        return Notification.objects.filter(user=user).order_by('-created_at')

class ChangeNotificationReadAPIView(UpdateAPIView):
    permission_classes = [IsAuthenticated, IsEmployee]
    serializer_class = NotificationReadSerializer
    
    def get_queryset(self):
        user = get_user(self.request)

        return Notification.objects.filter(user=user)


class ReadAllNotificationAPIView(APIView):
    permission_classes = [IsAuthenticated, IsEmployee]

    def get(self, request, *args, **kwargs):
        user = get_user(request)

        Notification.objects.filter(user=user).update(read=True)

        return Response({'Message': 'Success'}, status=status.HTTP_200_OK)
    
    def delete(self, request, *args, **kwargs):
        user = get_user(request)
        Notification.objects.filter(user=user).delete()
        return Response({'Message': 'Notification cleared successfully'}, status=status.HTTP_200_OK)


class AddFCMTokenAPIView(CreateAPIView):
    permission_classes = (IsAuthenticated, IsEmployee)
    serializer_class = FCMTokenSerializer
    queryset = FCMRegistrationToken.objects.all()

    def get_serializer_context(self):
        user = get_user(self.request)
        return {'user': user}


class SendNotificationToDevice(APIView):
    authentication_classes = ()
    permission_classes = ()

    def get(self, request, *args, **kwargs):
        url = 'https://fcm.googleapis.com/v1/{0}/messages:send'
        project_id = 'projects/meetingspace-271809'
        url = url.format(project_id)

        data = {
            'message': {
                'android': {
                    'notification': {
                        'title': 'Hello',
                        'body': 'Hello World. Please be safe during COVID-19.',
                        'image': 'https://i.ytimg.com/vi/NjAIipt3usw/maxresdefault.jpg'
                    },
                },
                'token': 'fHi8Lu7AHUaXmjpIclNd5H:APA91bFecJnDO3ZkaA_anHc3cUhcjXRd8WjhyWlltaYCFpmngTcOPhkeEBZ4alDLw-K_7segGTqcsfq5IlVsD1ET8GodOYTl1hWNSJ8bbv5YxblCmabp3U8qe8OVEvROoym_ik2dv1m_',
                'data': {
                    'meeting_id': 'Hello Hello'
                }
            }
        }

        headers = {
            'Authorization': 'Bearer {0}'.format(get_access_token()),
            'Content-Type': 'application/json; UTF-8',
        }

        resp = requests.post(url, data=json.dumps(data), headers=headers)
        return Response({'Message': resp.json()}, status=status.HTTP_200_OK)
