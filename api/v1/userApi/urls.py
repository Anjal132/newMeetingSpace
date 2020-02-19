"""
This is the root url router for all our User API's.
"""

from django.urls import include, path, re_path

from users.apiViews import LoginUserAPIView, PasswordResetConfirmAPIView, RefreshTokenAPIView, UpdateProfileAPIView

urlpatterns = [
    path('resetPassword/', PasswordResetConfirmAPIView.as_view()),
    path('login/', LoginUserAPIView.as_view()),
    path('refreshToken/', RefreshTokenAPIView.as_view()),
    path('updateProfile/<int:user>', UpdateProfileAPIView.as_view()),
]
