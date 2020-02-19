"""
This is the root url router for all our Super Staff API's.
"""

from django.urls import path, include
from organization.apiViews import CreateCompanyAPIView, ListCompanyAPIView, CompanyDetailAPIView

urlpatterns = [
    path('createCompany/', CreateCompanyAPIView.as_view()),
    path('viewCompany/', ListCompanyAPIView.as_view()),
    path('statusCompany/<slug:short_name>/', CompanyDetailAPIView.as_view()),
]

