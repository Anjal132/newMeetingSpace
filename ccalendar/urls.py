from django.urls import path

from .views import (GoogleLogoutAPIView, GoogleTokenStoreAPIView,
                    OutlookTokenStoreAPIView,
                    OutlookLogoutAPIView)

urlpatterns = [
    path('google/', GoogleTokenStoreAPIView.as_view()),
    path('outlook/', OutlookTokenStoreAPIView.as_view()),
    path('outlook/logout/', OutlookLogoutAPIView.as_view()),
    path('google/logout/', GoogleLogoutAPIView.as_view()),
]
