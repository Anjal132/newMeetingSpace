from django.urls import path

from notifications.views import (AllNotificationsAPIView,
                                 ChangeNotificationReadAPIView,
                                 NotificationReadAPIView,
                                 ReadAllNotificationAPIView, AddFCMTokenAPIView)

urlpatterns = [
    path('all/', AllNotificationsAPIView.as_view()),
    path('unread/', NotificationReadAPIView.as_view()),

    path('allnotifications/',ReadAllNotificationAPIView.as_view()),
    path('read/<int:pk>/', ChangeNotificationReadAPIView.as_view()),
    path('token/', AddFCMTokenAPIView.as_view()),
]
