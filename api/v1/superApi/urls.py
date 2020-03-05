"""
This is the root url router for all our Super Staff API's.
"""

from django.urls import include, path

from organization.apiViews import (CompanyDashboardAPIVew,
                                   CompanyDetailAPIView, CreateCompanyAPIView,
                                   ListCompanyAPIView)

urlpatterns = [
    path('createCompany/', CreateCompanyAPIView.as_view()),
    path('viewCompany/', ListCompanyAPIView.as_view()),
    path('statusCompany/<slug:short_name>/', CompanyDetailAPIView.as_view()),
    path('dashboard/', CompanyDashboardAPIVew.as_view())
]
