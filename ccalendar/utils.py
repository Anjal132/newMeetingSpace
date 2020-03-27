from urllib.parse import quote

import requests
from django.db.models.signals import post_save
from django.dispatch import receiver

from meeting.models import Host, Status

CLIENT_ID = '1e94c5aa-f9e8-46db-b73b-2878b6313cd2'
CLIENT_SECRET = 'ghPx.S81:D[7_gNz2.cLJR=ou:Z.=2eF'

GOOGLE_CLIENT_ID = '156351485709-nbf2vn6f143hnal97j11s876d9o2lr0n.apps.googleusercontent.com'
GOOLGLE_CLIENT_SECRET = 'w7vAxkzKuAi-e0Ls4fQTuwIk'

GOOGLE_TOKEN_URI = 'https://oauth2.googleapis.com/token'

AUTHORITY = 'https://login.microsoftonline.com'
TOKEN_URL = '{0}{1}'.format(AUTHORITY, '/common/oauth2/v2.0/token')

SCOPES = [
    'openid',
    'User.Read',
    'offline_access',
    'Calendars.Read',
]

def get_token_from_code(auth_code, redirect_uri):
    print(auth_code)
    post_data = {
        'grant_type':'authorization_code',
        'code':quote(auth_code),
        'redirect_uri':redirect_uri,
        'scope': ' '.join(str(i) for i in SCOPES),
        'client_id':quote(CLIENT_ID),
        'client_secret':CLIENT_SECRET

    }

    res = requests.post(TOKEN_URL, data=post_data)
    print(res.json())

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

