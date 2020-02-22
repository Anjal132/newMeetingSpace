from django.urls import path

from .views import (AcceptMeetingAPIView, DeclineMeetingAPIView,
                    HostFinalizeMeetingAPIView, HostMeetingView,
                    HostPostponeMeetingAPIView, MeetingFinalizeAPIView,
                    MeetingOnDateAPIView, PostponeMeetingAPIView,
                    UpcomingMeetingsAPIView, HostPostponeFinalizeMeetingAPIView)

urlpatterns = [
    path('v1/host/', HostMeetingView.as_view()),
    path('v1/hosted/', UpcomingMeetingsAPIView.as_view()),
    path('v1/finalize/', MeetingFinalizeAPIView.as_view()),
    path('v1/accept/', AcceptMeetingAPIView.as_view()),
    path('v1/decline/', DeclineMeetingAPIView.as_view()),
    path('v1/postpone/', PostponeMeetingAPIView.as_view()),
    path('v1/status/', HostFinalizeMeetingAPIView.as_view()),
    path('v1/date/', MeetingOnDateAPIView.as_view()),
    path('v1/postponeMeeting/<slug:uid>/', HostPostponeMeetingAPIView.as_view()),
    path('v1/finalizePostpone/<slug:meeting>/', HostPostponeFinalizeMeetingAPIView.as_view())

]
