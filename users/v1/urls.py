''' This is the (V1) URL files for the auth functionality of meetingSpace project '''

from rest_framework import routers
from users.v1.apiViews import AuthViewSet

ROUTER = routers.SimpleRouter(trailing_slash=False)
ROUTER.register('', AuthViewSet, basename='auth')

urlpatterns = ROUTER.urls
