"""
This is the root url router for all our V1 API's.
"""

from django.urls import path, include

urlpatterns = [
    # path('user/', include('api.v1.userApi.urls')),
    # path('admins/', include('api.v1.adminApi.urls')),
    path('super/', include('api.v1.superApi.urls')),
    # path('property/', include('property.urls')),
]