import base64
import datetime
import os

import requests

from urllib.parse import urlencode

from core.models import *

class SpotifyAPI(object):
    access_token = None
    access_token_expires = datetime.datetime.now()
    access_token_did_expire = True

    client_id = None
    client_secret = None

    code = None

    user = None

    token_url = "https://accounts.spotify.com/api/token"
    scopes = ''

    def __init__(self, client_id, client_secret, user, code, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.client_id = client_id
        self.client_secret = client_secret

        self.code = code

        self.user = user

    def auth_user(self):
        self.scopes = 'streaming app-remote-control'

    def get_client_credentials(self):
        client_id = self.client_id
        client_secret = self.client_secret

        if not client_secret or not client_id:
            raise Exception("You must set client_id and client_secret")

        client_creds = f"{client_id}:{client_secret}"
        client_creds_b64 = base64.b64encode(client_creds.encode())

        return client_creds_b64.decode()

    def get_token_headers(self):
        client_creds_b64 = self.get_client_credentials()

        return {
            "Authorization": f"Basic {client_creds_b64}"
        }

    def get_token_data(self):
        return {
            "grant_type": "client_credentials"
        }

    def perform_auth(self):
        token_url = self.token_url
        token_data = self.get_token_data()
        token_headers = self.get_token_headers()

        r = requests.post(token_url, data=token_data, headers=token_headers)

        if r.status_code not in range(200, 299):
            raise Exception("Could not authenticate client.")

        data = r.json()

        now = datetime.datetime.now()

        access_token = data['access_token']
        expires_in = data['expires_in']  # seconds

        expires = now + datetime.timedelta(seconds=expires_in)

        self.access_token = access_token
        self.access_token_expires = expires
        self.access_token_did_expire = expires < now

        return True

    def perform_user_auth(self):
        redirect_uri = 'http://localhost:8000/callback/' if os.environ.get('DJANGO_DEVELOPMENT') else 'https://mixjam.io/callback/'

        token_data = {
            'code': self.code,
            'redirect_uri': redirect_uri,
            'grant_type': 'authorization_code'
        }

        token_headers = self.get_token_headers()

        r = requests.post(self.token_url, data=token_data, headers=token_headers)

        if r.status_code not in range(200, 299):
            print(r.json())

            raise Exception("Could not authenticate client.")

        data = r.json()

        self.user.userprofile.access_token = data['access_token']
        self.user.userprofile.refresh_token = data['refresh_token']
        self.user.userprofile.save()

    def get_access_token(self):
        token = self.access_token
        expires = self.access_token_expires

        now = datetime.datetime.now()

        if expires < now:
            self.perform_auth()

            return self.get_access_token()
        elif not token:
            self.perform_auth()

            return self.get_access_token()

        return token

    def get_resource_header(self):
        access_token = self.get_access_token()

        headers = {
            "Authorization": f"Bearer {access_token}"
        }

        return headers
    def get_user_auth_header(self):
        access_token = self.user.userprofile.access_token

        headers = {
            "Authorization": f"Bearer {access_token}"
        }

        return headers