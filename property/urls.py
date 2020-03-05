from django.urls import path

from .views import (AllBuildingAllDepartmentView, AllRoomsAPIView,
                    AvailableRoomsAPIView, DepartmentDetailView,
                    DepartmentUpdateDeleteView, DepartmentView,
                    PropertyAddView, PropertyDetailAPIView, RoomAddView,
                    RoomDetailsAPIView, AllRoomsAPIViewWithoutPagination, RoomUpdateAPIView)

urlpatterns = [
    path('', PropertyAddView.as_view()),
    path('<int:pk>/', PropertyDetailAPIView.as_view()),

    path('all/', AllBuildingAllDepartmentView.as_view()),
    path('department/', DepartmentView.as_view()),
    path('department/<int:pk>/', DepartmentUpdateDeleteView.as_view()),
    path('departmentmembers/', DepartmentDetailView.as_view()),

    path('room/', RoomAddView.as_view()),
    path('room/<int:pk>/', RoomDetailsAPIView.as_view()),
    path('room/update/<int:pk>/', RoomUpdateAPIView.as_view()),
    path('room/all/', AllRoomsAPIView.as_view()),
    path('room/allroomswithoutpagination/', AllRoomsAPIViewWithoutPagination.as_view()),
    path('room/available/', AvailableRoomsAPIView.as_view()),
]
