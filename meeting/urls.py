from django.urls import path

from .views import (ChangeParticipantStatusAPIView, HostMeetingView,
                    HostPostponeMeetingAPIView,
                    MeetingOnDateAPIView,
                    UpcomingMeetingsAPIView, HostPostponeFinalizeMeetingAPIView, ChangeHostStatusAPIView)

urlpatterns = [
    path('v1/host/', HostMeetingView.as_view()),
    path('v1/host/status/', ChangeHostStatusAPIView.as_view()),
    path('v1/hosted/', UpcomingMeetingsAPIView.as_view()),
    
    path('v1/participant/status/', ChangeParticipantStatusAPIView.as_view()),
    path('v1/date/', MeetingOnDateAPIView.as_view()),
    path('v1/postponeMeeting/<slug:uid>/',
         HostPostponeMeetingAPIView.as_view()),
    path('v1/finalizePostpone/<slug:meeting>/',
         HostPostponeFinalizeMeetingAPIView.as_view())
]
