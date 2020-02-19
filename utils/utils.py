from datetime import timedelta

import jwt
from django.conf import settings
from django.contrib.auth import authenticate
from django.contrib.auth.models import Group
from django.contrib.auth.tokens import default_token_generator
from django.utils.encoding import force_text
from django.utils.http import urlsafe_base64_decode
from rest_framework import exceptions, serializers

from organization.models import Organization
from users.models import User

from .otherUtils import send_mail_employee


def get_all_user(object):
    user = get_user(object)
    if user.is_staff:
        org = Organization.objects.all()
        detail = list(org)
        data = {}
        details = []
        for indi in detail:
            
            admin = indi.company_admin.all().values('id')
            if admin:
                for eac in admin:
                    details.append(eac['id'])
        return True

def get_user(object):
    payload = decode_jwt_cookie(object)

    try:
        user = User.objects.get(uid = payload['id'])
    except User.DoesNotExist:
        msg = 'No user matching this token was found.'
        raise exceptions.AuthenticationFailed(msg)
    return user



def decode_jwt_cookie(object):
    try:
        token = object.COOKIES.get('token')
    except:
        msg = 'There is no Authorization token in the cookie'
        raise exceptions.AuthenticationFailed(msg)
    
    payload = decode_jwt(token)
    
    return payload


def verify_further(employee, organization):
    try:
        if organization == employee.belongs_to.get():
            if not employee.is_verified:
                send_mail_employee(employee, organization)
                return True
            else:
                raise exceptions.ValidationError("The user has already confirmed the invitation")
        else:
            raise exceptions.ValidationError("The user doesn't belong to your organization")
    except:
        raise exceptions.ValidationError("The email doesn't belong to any user")


def decode_jwt(token):
    
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, leeway=timedelta(seconds=10), algorithms=['HS384'])
    except jwt.InvalidSignatureError:
        msg = "Invalid signature. The token has been tampered"
        raise exceptions.AuthenticationFailed(msg)
    except jwt.ExpiredSignature:
        msg = "The token has expired"
        raise exceptions.AuthenticationFailed(msg)
    except jwt.InvalidAlgorithmError:
        msg = "The token has invalid algorithm"
        raise exceptions.AuthenticationFailed(msg)
    except:
        msg = "The token can't be decoded"
        raise exceptions.AuthenticationFailed(msg)

    return payload

def get_user_by_email(email):
    try:
        user = User.objects.get(email=email)
    except:
        msg = 'There are no users, with the provided email address'
        raise exceptions.ValidationError(msg)
    return user

def create_user_account(request, data):
    return True


def get_company_name(object):

    payload = decode_jwt_cookie(object)
    uid = Group.objects.get(name="Admin_User").uid

    for group in payload['scopes']:
        if group == str(uid):
            company = Organization.objects.get(uid = payload['scopes'][group])
            if company:
                return company
            else:
                raise exceptions.PermissionDenied("The user is not Admin of any company")
    raise exceptions.PermissionDenied('The user is not Admin of any company')



def authenticate_user(email, password):

    user = authenticate(username=email, password=password)

    if user is None:
        raise serializers.ValidationError(
            'Does\'nt match with any existing user')

    if not user.is_active:
        raise serializers.ValidationError('The user account is disabled')

    if not user.is_verified:
        raise serializers.ValidationError('The user account is not verified')

    return user





def get_user_for_password_reset_token(uidb64, token):
    default_error_messages = {
        'invalid_token': 'Invalid token or the token has expired',
        'user_not_found': 'No user exists for given token'
    }
    try:
        if uidb64 is None:
            raise serializers.ValidationError(
                default_error_messages['invalid_token'])

        if token is None:
            raise serializers.ValidationError(
                default_error_messages['invalid_token'])

        user_uid = force_text(urlsafe_base64_decode(uidb64))
        user = User.objects.get(uid=user_uid)

        if not default_token_generator.check_token(user, token):
            raise serializers.ValidationError(
                default_error_messages['invalid_token'])

        return user

    except ValueError:
        raise serializers.ValidationError(
            default_error_messages['invalid_token'])

    except(TypeError, OverflowError, User.DoesNotExist):
        raise serializers.ValidationError(
            default_error_messages['invalid_token'])





def verify_refresh(current_refresh_token):
    
    payload = decode_jwt(current_refresh_token)
    
    if payload['type'] == 'access':
        msg = "The token is a access token"
        raise exceptions.AuthenticationFailed(msg)

    # Extra logic required to verify refresh token
    # Later, (jti along with id) can be used to blacklist the token

    try:
        user = User.objects.get(uid=payload['id'])
    except:
        msg = "The token doesn't belong to any user"
        raise exceptions.AuthenticationFailed(msg)

    return user
