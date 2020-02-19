from datetime import timedelta

import jwt
from django.conf import settings
from rest_framework import exceptions
from rest_framework.authentication import BaseAuthentication

from users.models import User


class JWTAuthentication(BaseAuthentication):

    def authenticate(self, request):
        """
            This method will authenticate the user.    
        """

        request.user = None

        # Get the JWT access_token from cookies
        try:
            tokens  = request.COOKIES.get('token')
            # print("token" + tokens)
        except:
            msg = "You do not have any token credentials"
            raise exceptions.AuthenticationFailed(msg)

        return self._authenticate_credentials(request, tokens)
    
    def _authenticate_credentials(self, request, token):
        """
            Try to authenticate the given credentials.
        """

        try:
            payload = jwt.decode(token, settings.SECRET_KEY, leeway=timedelta(seconds=10), algorithms=['HS384'])
        except jwt.InvalidSignatureError:
            msg = "Invalid signature. The token has been tampered"
            raise exceptions.AuthenticationFailed(msg)
        except jwt.ExpiredSignature:
            msg = "The token has expired"
            raise exceptions.AuthenticationFailed(msg)
        except:
            msg = "The token can't be decoded"
            raise exceptions.AuthenticationFailed(msg)
        

        if payload['type'] == 'refresh':
            msg = "The token is a refresh token"
            raise exceptions.AuthenticationFailed(msg)


        try:
            user = User.objects.get(uid = payload['id'])
        except User.DoesNotExist:
            msg = 'No user matching this token was found.'
            raise exceptions.AuthenticationFailed(msg)
        

        if not user.is_active:
            msg = 'This user has been deactivated.'
            raise exceptions.AuthenticationFailed(msg)
        

        return (user, token)
