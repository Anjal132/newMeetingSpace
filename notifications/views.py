from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.generics import ListAPIView, UpdateAPIView

from permission.permissions import IsEmployee
from utils.utils import get_user

from notifications.models import Notification
from notifications.serializers import NotificationSerializer, NotificationReadSerializer

# Create your views here.

class NotificationReadAPIView(APIView):
    permission_classes = [IsAuthenticated, IsEmployee]

    def get(self, request, *args, **kwargs):
        user = get_user(request)
        unread = Notification.objects.filter(user=user).filter(read=False)

        return Response({'Unread':unread.exists()}, status=status.HTTP_200_OK)


class AllNotificationsAPIView(ListAPIView):
    permission_classes = [IsEmployee, IsAuthenticated]
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


