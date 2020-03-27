from oauth2client.service_account import ServiceAccountCredentials


SCOPES = {
    'https://www.googleapis.com/auth/firebase.messaging'
}

def get_access_token():
    '''Retrieve a valid access token to authorize requests to firebase
       for cloud messaging.

       :return: Access token
    '''

    credentials = ServiceAccountCredentials.from_json_keyfile_name(
        'service-account.json', scopes=SCOPES
    )
    access_token_info = credentials.get_access_token()
    return access_token_info.access_token
