from django.urls import path

from .views import (AcceptMeetingAPIView, DeclineMeetingAPIView,
                    HostFinalizeMeetingAPIView, HostMeetingView,
                    MeetingFinalizeAPIView, MeetingOnDateAPIView,
                    PostponeMeetingAPIView, UpcomingMeetingsAPIView)

urlpatterns = [
    path('v1/host/', HostMeetingView.as_view()),
    path('v1/hosted/', UpcomingMeetingsAPIView.as_view()),
    path('v1/finalize/', MeetingFinalizeAPIView.as_view()),
    path('v1/accept/', AcceptMeetingAPIView.as_view()),
    path('v1/decline/', DeclineMeetingAPIView.as_view()),
    path('v1/postpone/', PostponeMeetingAPIView.as_view()),
    path('v1/status/', HostFinalizeMeetingAPIView.as_view()),
    path('v1/date/', MeetingOnDateAPIView.as_view()),
]
