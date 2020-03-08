"""
This is the root url router for all our Company Admin API's.
"""

from django.urls import path, include
from organization.apiViews import AdminDashboardAPIView
# from users.v1.apiViews import RegisterEmployeeAPIView

urlpatterns = [
    path('dashboard/', AdminDashboardAPIView.as_view()),
    # path('createEmployee', RegisterEmployeeAPIView.as_view())
]