from django.urls import include, path

# from users.v1.apiViews import GetUsersSchemaAPIView
from users.views import (GetProfileAPIView, GetSuggestionsAPIView,
                         GetUsersAPIView, UserDetailAPIView, AddBatchEmployeeAPIView, CheckJSONAPIView)

urlpatterns = [
    path('v1/', include('users.v1.urls')),
    path('v1/add_batch_users/', AddBatchEmployeeAPIView.as_view()),
    path('v1/profile/', GetProfileAPIView.as_view()),
    path('v1/suggestion/', GetSuggestionsAPIView.as_view()),

    path('v1/allusers/', GetUsersAPIView.as_view()),
    path('v1/user/<int:pk>/', UserDetailAPIView.as_view()),

    path('v1/checkjson', CheckJSONAPIView.as_view()),
]
