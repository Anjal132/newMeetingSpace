from django.urls import path

from groups.views import GroupAPIView

urlpatterns = [
    path('', GroupAPIView.as_view()),
]
