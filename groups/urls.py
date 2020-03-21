from django.urls import path

from groups.views import GroupAPIView, RemoveGroupAPIView

urlpatterns = [
    path('', GroupAPIView.as_view()),
    path('remove/<int:pk>/', RemoveGroupAPIView.as_view()),
]
