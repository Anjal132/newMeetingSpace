"""
This is the root url router for all our API's.
"""
from django.urls import path, include

urlpatterns = [
    path('auth/', include('users.urls')),
    path('admin/', include('api.v1.adminApi.urls')),
    path('super/', include('api.v1.superApi.urls')),
    path('meeting/', include('meeting.urls')),
    path('calendar/', include('ccalendar.urls')),
    path('property/', include('property.urls')),
    path('notification/', include('notifications.urls')),
    path('organization/', include('organization.urls')),
    path('group/', include('groups.urls')),
]
