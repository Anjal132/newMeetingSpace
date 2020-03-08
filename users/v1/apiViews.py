import json

from django.contrib.auth import user_logged_in
from django.http import HttpResponse
from django.core import serializers
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.generics import ListAPIView, RetrieveUpdateAPIView
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from meetingSpace.backend import JWTAuthentication
from permission.permissions import IsCompanyAdmin, IsEmployee
from staffProfile.models import StaffProfile
from userProfile.models import UserProfile
from users.v1.apiSerializers import (ChangePasswordSerializer,
                                     CreateEmployeeSerializer, EmptySerializer,
                                     LoginResponseSerializer, LoginSerializer,
                                     PasswordResetConfirmSerializer,
                                     RefreshTokenSerializer,
                                     ResetPasswordSerializer,
                                     StaffProfileDetailSerializer,
                                     StaffProfileSerializer,
                                     UserProfileDetailSerializer,
                                     UserProfileSerializer, UserSerializer)
from users.v1.mixin import MultipleSerializerMixin
from utils.otherUtils import send_password_reset_email
from utils.utils import (authenticate_user, get_all_user, get_company_name,
                         get_user, get_user_by_email,
                         get_user_for_password_reset_token, verify_further,
                         verify_refresh)


class AuthViewSet(MultipleSerializerMixin, viewsets.GenericViewSet):
    authentication_classes = (JWTAuthentication, )
    permission_classes = (AllowAny, )
    serializer_class = EmptySerializer
    serializer_classes = {
        'reset_password_confirm': PasswordResetConfirmSerializer,
        'resend_confirmation': ResetPasswordSerializer,
        'retrieve_profile': UserProfileSerializer,
        'get_user_detail': UserProfileDetailSerializer,
        'change_password': ChangePasswordSerializer,
        'reset_password': ResetPasswordSerializer,
        'update_profile': UserSerializer,
        'refresh_token': RefreshTokenSerializer,
        'add_employee': CreateEmployeeSerializer,
        'signin': LoginSerializer,
        'staff': StaffProfileSerializer,
        'user': UserProfileSerializer,
    }

    @action(methods=['GET', ], detail=False, lookup_field='id', permission_classes=(IsAuthenticated, ))
    def list_user(self, request):
        # serializer = self.get_serializer(data=request.data)
        return Response({"status": "Success"}, status=status.HTTP_204_NO_CONTENT)

    @action(methods=['POST', ], detail=False, authentication_classes=())
    def signin(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = authenticate_user(**serializer.validated_data)
        user_logged_in.send(sender=user.__class__,
                            request=self.request, user=user)
        data = LoginResponseSerializer(user).data
        cookie = 'token=' + data['access_token'] + \
            '; path=/; HttpOnly; max-age=86400; SameSite=None;'

        return Response(data, status=status.HTTP_200_OK, headers={'Set-Cookie': cookie})

    @action(methods=['POST', ], detail=False, permission_classes=[IsAuthenticated, ])
    def change_password(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = get_user(self.request)
        user.set_password(serializer.validated_data['new_password'])
        user.save()
        return Response({"status": "Success"}, status=status.HTTP_204_NO_CONTENT)

    @action(methods=['POST', ], detail=False, permission_classes=[IsAuthenticated, IsCompanyAdmin, ])
    def resend_confirmation(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        employee = get_user_by_email(serializer.validated_data['email'])
        organization = get_company_name(self.request)
        check = verify_further(employee, organization)
        if check:
            return Response({"status": "Success"}, status=status.HTTP_202_ACCEPTED)
        return Response({"status":"Failed"}, status=status.HTTP_400_BAD_REQUEST)

    @action(methods=['POST', ], detail=False, authentication_classes=())
    def reset_password(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = get_user_by_email(serializer.validated_data['email'])
        if not user.is_active:
            return Response({'Message': 'The user is not active. Contact your admin.'}, status=status.HTTP_400_BAD_REQUEST)
        send_password_reset_email(user)
        return Response(
            {"status": "Success",
                "message": "A password reset link has been sent to your email"},
            status=status.HTTP_200_OK
        )

    @action(methods=['POST', ], detail=False, authentication_classes=())
    def reset_password_confirm(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        password = serializer.validated_data.pop('password')
        user = get_user_for_password_reset_token(**serializer.validated_data)
        user.set_password(password)
        user.is_verified = True
        user.save()
        return Response({"status": "Success"}, status=status.HTTP_201_CREATED)

    @action(methods=['POST', ], detail=False, authentication_classes=())
    def refresh_token(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = verify_refresh(**serializer.validated_data)
        data = LoginResponseSerializer(user).data
        cookie = 'token=' + data['access_token'] + \
            '; path=/; HttpOnly; max-age=86400; SameSite=None;'
        return Response(data, status=status.HTTP_200_OK, headers={'Set-Cookie': cookie})

    @action(methods=['POST', ], detail=False, permission_classes=[IsAuthenticated, IsCompanyAdmin, ])
    def add_employee(self, request):
        print(request.data)
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({"success": "ok"}, status=status.HTTP_201_CREATED)

    @action(methods=['PUT', ], detail=False, lookup_field='user', permission_classes=[IsAuthenticated, IsEmployee])
    def update_profile(self, request):
        user = get_user(self.request)
        # user = UserProfile.objects.filter(user=get_user(self.request))
        serializer = self.get_serializer(instance=user, data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({"success": "ok"}, status=status.HTTP_201_CREATED)

    @action(methods=['GET', ], detail=False, permission_classes=[IsAuthenticated, ])
    def get_user_detail(self, request):
        user = get_user(self.request)
        if user.is_superuser:
            return Response({"message": "Superuser has no profile"})
        if user.is_staff:
            serializer = StaffProfileDetailSerializer(
                self.get_queryset().first())
        else:
            serializer = UserProfileDetailSerializer(
                self.get_queryset().first())
        return Response(serializer.data)

    @action(methods=['GET', ], detail=False, permission_classes=[IsAuthenticated, ])
    def retrieve_profile(self, request):
        data = serializers.serialize('json', self.get_queryset())
        return Response(json.loads(data), status=status.HTTP_201_CREATED)

    def get_serializer_context(self):
        if getattr(self, 'swagger_fake_view', False):
            return CreateEmployeeSerializer

        if self.action == 'add_employee':
            organization = get_company_name(self.request)
            return{"organization": organization}

        if self.action == 'change_password':
            user = get_user(self.request)
            return{"uid": user.uid}

    def get_queryset(self):
        if self.action in ('retrieve_profile', 'get_user_detail', 'update_profile'):
            user = get_user(self.request)
            if user.is_staff:
                return StaffProfile.objects.filter(user=user)
            else:
                return UserProfile.objects.filter(user=user)
        if self.action == 'list_user':
            user = get_all_user(self.request)

            return UserProfile.objects.filter(user_id__in=user)
