from django.urls import path
from organization.apiViews import CompanyProfileAPIView


urlpatterns = [
    path('profile/<slug:short_name>/', CompanyProfileAPIView.as_view()),
]
