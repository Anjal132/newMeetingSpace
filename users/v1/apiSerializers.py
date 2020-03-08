from datetime import datetime, timedelta

from django.conf import settings
from django.contrib.auth import password_validation
from django.db import connection
from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from rest_framework.validators import UniqueValidator

from ccalendar.models import Google, Outlook
from organization.apiSerializers import CompanyDetailSerializer
from staffProfile.models import StaffProfile
from userProfile.models import UserProfile
from users.models import User


class ActiveInactiveUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('is_active',)
    
    def update(self, instance, validated_data):
        instance.is_active = validated_data['is_active']
        instance.temp_active_status = validated_data['is_active']
        instance.save()
        return instance

class UserListSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'email', 'is_active', 'is_verified')


class UserDetailSerializer(serializers.ModelSerializer):
    """Serializer for user"""
    belongs_to = CompanyDetailSerializer(required=True, many=True)

    class Meta:
        model = User
        fields = ('email', 'belongs_to')


class UserProfileSerializer(serializers.ModelSerializer):
    # building = serializers.SlugRelatedField(read_only=True, slug_field='building')
    # department = serializers.SlugRelatedField(read_only=True, slug_field='department')
    """Serializer for User's profile"""
    class Meta:
        model = UserProfile
        fields = ('building', 'department', 'first_name',
                  'middle_name', 'last_name', 'profile_pics')
        # fields = '__all__'


class UserSerializer(serializers.ModelSerializer):
    """Serializer for User's profile"""

    class Meta:
        model = UserProfile
        fields = ('first_name', 'last_name', 'middle_name',
                  'internationalization', 'profile_pics')


class UserProfileDetailSerializer(serializers.ModelSerializer):
    """Serializer for User's profile"""

    # user = UserDetailSerializer(required=True)
    building = serializers.SlugRelatedField(slug_field='name', read_only=True)
    department = serializers.SlugRelatedField(
        slug_field='department_name', read_only=True)
    room = serializers.SlugRelatedField(
        slug_field='room_number', read_only=True)
    floor = serializers.SerializerMethodField()
    google_sign_in = serializers.SerializerMethodField()
    outlook_sign_in = serializers.SerializerMethodField()
    floors = serializers.SerializerMethodField()
    office_start_time = serializers.TimeField(format='%I:%M %p')
    office_end_time = serializers.TimeField(format='%I:%M %p')

    class Meta:
        model = UserProfile
        fields = ('room', 'floor', 'floors', 'building', 'department', 'first_name', 'middle_name',
                  'last_name', 'internationalization', 'profile_pics', 'google_sign_in', 'outlook_sign_in',
                  'office_start_time', 'office_end_time')

    def get_floor(self, obj):
        if obj.room is not None:
            return obj.room.floor
        return None

    def get_floors(self, obj):
        if obj.building is not None:
            return obj.building.shared_company_floors
        return None

    def get_google_sign_in(self, obj):
        # user = get_user(self.request)
        user = User.objects.get(email=obj)

        if Google.objects.filter(user=user).exists():
            goo = Google.objects.get(user=user)
            return goo.email
        return "False"

    def get_outlook_sign_in(self, obj):
        user = User.objects.get(email=obj)

        if Outlook.objects.filter(user=user).exists():
            return "True"
        return "False"


class StaffProfileDetailSerializer(serializers.ModelSerializer):
    """Serializer for User's profile"""
    user = UserDetailSerializer(required=True)

    class Meta:
        model = StaffProfile
        fields = ('first_name', 'middle_name', 'last_name',
                  'internationalization', 'profile_pics', 'user')


class StaffProfileSerializer(serializers.ModelSerializer):
    """Serializer for Staff's profile"""
    class Meta:
        model = StaffProfile
        fields = "__all__"


class ResetPasswordSerializer(serializers.Serializer):
    """ Serializer to reset the own's password """
    email = serializers.EmailField(required=True)


class ChangePasswordSerializer(serializers.Serializer):
    """ Serializer to change the user password """

    old_password = serializers.CharField(required=True, write_only=True)
    new_password = serializers.CharField(required=True, write_only=True)

    def validate_old_password(self, value):
        user = User.objects.get(uid=self.context['uid'])
        if not user.check_password(value):
            raise serializers.ValidationError(
                'Current password does not match')
        return value

    def validate_new_password(self, value):
        password_validation.validate_password(value)
        return value


class CreateEmployeeSerializer(serializers.ModelSerializer):
    """Serializer to invite the employee by Company Admin."""

    msg = 'The user with this email is already invited'
    usr = User.objects.all()
    email = serializers.EmailField(required=True, validators=[
        UniqueValidator(usr, msg)])

    class Meta:
        """ This is the Meta Class for Model Serializer"""

        model = User
        fields = ['email', ]

    def create(self, validated_data):
        validated_data['organization'] = self.context['organization']
        user = User.objects.create_user(**validated_data)

        return user


class PasswordResetConfirmSerializer(serializers.Serializer):
    '''This is the serializer to reset the user's password.'''

    password = serializers.CharField(required=True, write_only=True)
    uidb64 = serializers.CharField(required=True, write_only=True)
    token = serializers.CharField(required=True, write_only=True)

    def validate_password(self, value):
        password_validation.validate_password(value)
        return value


class LoginSerializer(serializers.Serializer):
    '''This is the serializer class for getting user credentials to authenticate the user'''

    email = serializers.CharField(required=True)
    password = serializers.CharField(required=True)


class LoginResponseSerializer(serializers.Serializer):
    '''This is the serializer class to serialize the tokens to send to the user'''

    access_token = serializers.SerializerMethodField()
    refresh_token = serializers.SerializerMethodField()
    expiry_time = serializers.SerializerMethodField()
    schema_name = serializers.SerializerMethodField()
    user_type = serializers.SerializerMethodField()
    profile_set = serializers.SerializerMethodField()
    workplace_set = serializers.SerializerMethodField()

    def get_schema_name(self, obj):
        return obj.temp_name

    def get_access_token(self, obj):
        '''Get's the access token for current user'''
        return obj.access_token

    def get_refresh_token(self, obj):
        '''Get's the refresh token for current user'''
        return obj.refresh_token

    def get_expiry_time(self, obj):
        '''Get's the expiry time of current access token for current user's request'''
        dt = datetime.now() + timedelta(minutes=(settings.ACCESS_TOKEN_EXPIRY_TIME-2))
        return int(dt.strftime('%s'))

    def get_user_type(self, obj):
        group = 'Not Found'
        user_groups = obj.groups.values_list('name', flat=True)
        user_groups_as_list = list(user_groups)
        if('Staff_User' in user_groups_as_list):
            group = 'Superuser'
        elif('Admin_User' in user_groups_as_list):
            group = 'CompanyAdmin'
        elif('Employee_User' in user_groups_as_list):
            group = 'Employee'
        return group

    def get_profile_set(self, obj):
        if obj.temp_name != 'public':
            connection.set_schema(schema_name=obj.temp_name)
            user_profile = UserProfile.objects.get(user=obj)

            if user_profile.get_full_name is not None:
                return True

            return False
        return True
    
    def get_workplace_set(self, obj):
        if obj.temp_name != 'public':
            connection.set_schema(schema_name=obj.temp_name)
            user_profile = UserProfile.objects.get(user=obj)

            if user_profile.building is not None:
                return True

            return False
        return True


class RefreshTokenSerializer(serializers.Serializer):
    '''
        This is the serializer to get the new access and refresh token using old refresh token.
    '''
    current_refresh_token = serializers.CharField(
        required=True, write_only=True)


class EmptySerializer(serializers.Serializer):
    pass
