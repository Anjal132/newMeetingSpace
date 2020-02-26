from django.urls import path
from organization.apiViews import CompanyProfileAPIView


urlpatterns = [
    path('profile/', CompanyProfileAPIView.as_view()),
]
