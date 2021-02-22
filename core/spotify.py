import base64
import json

import requests

client_id = '8b817932e631474cb15f7e36edcfc53b'
client_secret = '6ef495db91bd4268b520f861117d39f9'

song_endpoint = 'https://api.spotify.com/v1/me/player/currently-playing'
player_endpoint = 'https://api.spotify.com/v1/me/player/'
playlist_endpoint = 'https://api.spotify.com/v1/playlists/'
refresh_endpoint = 'https://accounts.spotify.com/api/token'

def get_headers(user):
    return {
        "Authorization": f"Bearer {user.userprofile.access_token}"
    }

def get_token_headers():
    client_creds_b64 = get_client_credentials()

    return {
        "Authorization": f"Basic {client_creds_b64}"
    }

def get_client_credentials():
    if not client_secret or not client_id:
        raise Exception("You must set client_id and client_secret")

    client_creds = f"{client_id}:{client_secret}"
    client_creds_b64 = base64.b64encode(client_creds.encode())

    return client_creds_b64.decode()

def refresh_token(user):
    print('NEEDS REFRESH')

    response = requests.post(refresh_endpoint, data = {
        'grant_type': 'refresh_token',
        'refresh_token': user.userprofile.refresh_token
    }, headers = get_token_headers())

    r_json = response.json()

    print(r_json)

    user.userprofile.access_token = r_json['access_token']
    user.userprofile.save()

    return response.status_code

def get(user, endpoint):
    response = requests.get(endpoint, headers = get_headers(user))

    if response.status_code == 401:
        refresh_token(user)

        response = requests.get(endpoint, headers=get_headers(user))

    return response

def put(user, endpoint, data):
    data = json.dumps(data)

    response = requests.put(endpoint, data = data, headers = get_headers(user))

    if response.status_code == 401:
        refresh_token(user)

        response = requests.put(endpoint, data = data, headers = get_headers(user))

    return response

def post(user, endpoint, data):
    data = json.dumps(data)

    response = requests.post(endpoint, data = data, headers = get_headers(user))

    if response.status_code == 401:
        refresh_token(user)

        response = requests.post(endpoint, data = data, headers = get_headers(user))

    return response

def get_playlist_data(user, playlist_id):
    playlist_data = get(user, playlist_endpoint + playlist_id)

    return playlist_data.json()

def get_song_data(user):
    song_data = get(user, song_endpoint)

    return song_data.json()