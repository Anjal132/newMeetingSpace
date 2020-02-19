from urllib.parse import quote
from django.dispatch import receiver
from django.db.models.signals import post_save
from meeting.models import Host, Status

import requests

CLIENT_ID = '51ada4be-c32e-4b21-8a82-04606b62bdfe'
CLIENT_SECRET = '6L6KsI=9H7.znviO]tubgvLVjJt/===K'

GOOGLE_CLIENT_ID = '60821597216-55fc0nt8aqmc1tgj4agpvaa1lma9ps6j.apps.googleusercontent.com'
GOOLGLE_CLIENT_SECRET = 'BPA6_Fbn5twtpJgLWwPsv_iy'

GOOGLE_TOKEN_URI = 'https://oauth2.googleapis.com/token'

AUTHORITY = 'https://login.microsoftonline.com'
TOKEN_URL = '{0}{1}'.format(AUTHORITY, '/common/oauth2/v2.0/token')

SCOPES = [
    'openid',
    'User.Read',
    'offline_access',
    'Calendars.Read',
    'Calendars.Read.Shared'
]

def get_token_from_code(auth_code, redirect_uri):
    post_data = {
        'grant_type':'authorization_code',
        'code':quote(auth_code),
        'redirect_uri':redirect_uri,
        'scope': ' '.join(str(i) for i in SCOPES),
        'client_id':quote(CLIENT_ID),
        'client_secret':CLIENT_SECRET

    }

    res = requests.post(TOKEN_URL, data=post_data)

    try:
        return res.json()
    except:
        return 'Error retrieving token {0} - {1}'.format(res.status_code, res.text)


def get_token_from_code_google(auth_code, redirect_uri):
    post_data = {
        'grant_type':'authorization_code',
        'code':quote(auth_code),
        'client_id':quote(GOOGLE_CLIENT_ID),
        'client_secret':GOOLGLE_CLIENT_SECRET,
        'redirect_uri':redirect_uri,
        'access_type':'offline',
    }

    res = requests.post(GOOGLE_TOKEN_URI, post_data)
    print(res.text)

    try:
        return res.json()
    except:
        return 'Error'


def refresh_token_from_google(refresh_token, redirect_uri):
    post_data = {
        'grant_type':'refresh_token',
        'refresh_token':refresh_token,
        'client_id':GOOGLE_CLIENT_ID,
        'client_secret':GOOLGLE_CLIENT_SECRET,
        'redirect_uri':redirect_uri
    }

    res = requests.post(GOOGLE_TOKEN_URI, post_data)
    print(res.text)

    try:
        return res.json()
    except:
        return 'Error'


