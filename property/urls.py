from django.urls import path

from .views import (AllBuildingAllDepartmentView, AllRoomsAPIView,
                    AvailableRoomsAPIView, DepartmentView, PropertyAddView,
                    PropertyDetailAPIView, RoomAddView, RoomDetailsAPIView, DepartmentDetailView)

urlpatterns = [
    path('', PropertyAddView.as_view()),
    path('<int:pk>/', PropertyDetailAPIView.as_view()),

    path('all/', AllBuildingAllDepartmentView.as_view()),
    path('department/', DepartmentView.as_view()),
    path('departmentmembers/', DepartmentDetailView.as_view()),

    path('room/', RoomAddView.as_view()),
    path('room/<int:pk>/', RoomDetailsAPIView.as_view()),
    path('room/all/', AllRoomsAPIView.as_view()),
    path('room/available/', AvailableRoomsAPIView.as_view()),
]
