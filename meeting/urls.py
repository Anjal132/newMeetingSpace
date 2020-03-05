from django.urls import path

from .views import (ChangeMeetingStatusAPIView,
                    HostFinalizeMeetingAPIView, HostMeetingView,
                    HostPostponeMeetingAPIView,
                    MeetingOnDateAPIView,
                    UpcomingMeetingsAPIView, HostPostponeFinalizeMeetingAPIView)

urlpatterns = [
    path('v1/host/', HostMeetingView.as_view()),
    path('v1/hosted/', UpcomingMeetingsAPIView.as_view()),
    path('v1/participant/status/', ChangeMeetingStatusAPIView.as_view()),
    path('v1/status/', HostFinalizeMeetingAPIView.as_view()),
    path('v1/date/', MeetingOnDateAPIView.as_view()),
    path('v1/postponeMeeting/<slug:uid>/', HostPostponeMeetingAPIView.as_view()),
    path('v1/finalizePostpone/<slug:meeting>/', HostPostponeFinalizeMeetingAPIView.as_view())
]
