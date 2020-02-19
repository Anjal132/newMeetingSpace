from rest_framework import permissions
from django.contrib.auth.models import Group
from utils.utils import decode_jwt_cookie

class IsStaffUser(permissions.BasePermission):
    def has_permission(self, request, view):

        payload = decode_jwt_cookie(request)

        uid = Group.objects.get(name="Staff_User").uid
        for scope in payload['scopes']:
            if scope == str(uid):
                return True
        return False

class IsCompanyAdmin(permissions.BasePermission):
    def has_permission(self, request, view):

        payload = decode_jwt_cookie(request)
        uid = Group.objects.get(name="Admin_User").uid
        for scope in payload['scopes']:
            if scope == str(uid):
                return True

        return False


class IsEmployee(permissions.BasePermission):
    def has_permission(self, request, view):

        payload = decode_jwt_cookie(request)
        uid = Group.objects.get(name="Employee_User").uid
        for scope in payload['scopes']:
            if scope == str(uid):
                return True

        return False
        