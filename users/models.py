import json
import uuid
from datetime import datetime, timedelta

import jwt
from django.conf import settings
from django.contrib.auth.models import (AbstractBaseUser, Group,
                                        PermissionsMixin)
from django.core import serializers
from django.core.mail import send_mail
from django.db import models

import organization.models as mod
from users.manager import UsersManager
from utils.utilsSerializers import GroupSerializer, UUIDEncoder

# Create your models here.




class User(AbstractBaseUser, PermissionsMixin):
    """
    This is the Custom User model for Meeting space project.

    This models consists of email, is_verified, is_staff, date_joined field along with
    user and group permission related to user.  
    """

    Group.add_to_class('uid', models.UUIDField(default=uuid.uuid4, unique=True, editable=False, db_index=True))

    email           = models.EmailField(db_index=True, unique=True)   
    uid             = models.UUIDField(default=uuid.uuid4, unique=True, editable=False, db_index=True)
    is_staff        = models.BooleanField(default=False)
    is_active       = models.BooleanField(default=True)
    is_verified     = models.BooleanField(default=False)
    date_joined     = models.DateTimeField(auto_now_add=True)
    temp_name       = models.CharField(max_length=20, null=True)
    belongs_to      = models.ManyToManyField(to='organization.Organization', related_name='user_belong', blank=True)
    temp_active_status = models.BooleanField(default=True)

    objects = UsersManager()

    # Unique identifier to use while login
    USERNAME_FIELD = 'email' 
    
    # Additional reuired fields while creating super user, apart from 'Email and Password'
    REQUIRED_FIELD = []

    def __str__(self):
        """
        Identifier for each object/row
        """
        return self.email

    def email_user(self, subject, message, from_email=None, **kwargs):
        """
        Sends an email to this User.
        """
        send_mail(subject, message, from_email, [self.email], **kwargs)

    @property
    def access_token(self):
        '''
        This method is used to generate the access_token for the user.
        '''
        return self._generate_access_token()
    
    @property
    def refresh_token(self):
        '''
        This method is used to generate the refresh_token for the user.
        '''
        return self._generate_refresh_token()

    def _generate_access_token(self):
        ''' 
        Generates the access token with the `expiry`, `user's uid`, `user's group`, and `user's company`.
        '''

        groups = [d['uid'] for d in GroupSerializer().serialize(self.groups.all(), fields=('uid'))]
        jsondata = {}

        for group in groups:
            group_name = Group.objects.get(uid=group)    

            if group_name.name == 'Admin_User':
                company = mod.Organization.objects.get(company_admin=self.id)
                jsondata[group] = str(company.uid)

            elif group_name.name == 'Employee_User':
                user = User.objects.get(uid=self.uid)
                company = user.belongs_to.get()
                if not company:
                    jsondata[group] = 'None'
                else:
                    jsondata[group] = str(company.uid)
            else:
                    jsondata[group] = 'None'


        dt = datetime.now() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRY_TIME)
        token = jwt.encode({
            'id': str(self.uid),
            'exp': int(dt.strftime('%s')),
            'iat': int(datetime.now().strftime('%s')),
            'type': 'access',
            'scopes': jsondata
            # 'scopes': [d['uid'] for d in GroupSerializer().serialize(self.groups.all(), fields=('uid'))]
        }, settings.SECRET_KEY, algorithm='HS384')

        return token.decode('utf-8')
        
    def _generate_refresh_token(self):
        ''' 
        Generates the refresh token with the `expiry`.
        '''
        dt          = datetime.now() + timedelta(days=settings.REFRESH_TOKEN_EXPIRY_TIME)
        unique_id   = str(uuid.uuid4())

        token = jwt.encode({
            'exp': int(dt.strftime('%s')),
            'iat': int(datetime.now().strftime('%s')),
            'type': 'refresh',
            'id': str(self.uid),
            'jti': unique_id

        }, settings.SECRET_KEY, algorithm='HS384')
        
        return token.decode('utf-8')
