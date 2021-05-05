import os
import base64
import json
import requests
import time

from django.utils import timezone

client_id = os.environ.get('CLIENT_ID')
client_secret = os.environ.get('CLIENT_SECRET')

player_endpoint = 'https://api.spotify.com/v1/me/player/'

song_endpoint = 'https://api.spotify.com/v1/me/player/currently-playing'
playlist_endpoint = 'https://api.spotify.com/v1/playlists/'
refresh_endpoint = 'https://accounts.spotify.com/api/token'

play_endpoint = 'https://api.spotify.com/v1/me/player/play'
pause_endpoint = 'https://api.spotify.com/v1/me/player/pause'
seek_endpoint = 'https://api.spotify.com/v1/me/player/seek'
previous_endpoint = 'https://api.spotify.com/v1/me/player/previous'
next_endpoint = 'https://api.spotify.com/v1/me/player/next'

def update_playlist(user, room, request_data):
    action = request_data['action']
    action_data = request_data['action_data']

    if action == 'play':
        room.playlist.playing = True
    elif action == 'pause':
        room.playlist.playing = False

        room.playlist.progress_ms = get_progress(room)
    elif action == 'play_direct' or action == 'previous' or action == 'next':
        room.playlist.progress_ms = 0
    
    room.playlist.last_action = timezone.now()
    room.playlist.save()

    print('""""" PLAYLIST UPDATE """""')
    print('PLAYING: ' + str(room.playlist.playing))
    print('SONG INDEX: ' + str(room.playlist.song_index))
    print('PROGRESS(MS): ' + str(room.playlist.progress_ms))
    print('LAST ACTION: ' + str(room.playlist.last_action))
    print('"""""""""""""""""""""""""""')

def action(user, room, request_action, action_data = None):
    print('BEFORE: ' + request_action + ' FOR @' + str(user.username))

    if request_action == 'play':
        play(user, room)
    elif request_action == 'play_direct':
        play_direct(user, room, action_data)
    elif request_action == 'pause':
        pause(user, room)
    elif request_action == 'seek':
        seek(user, action_data)
    elif request_action == 'previous':
        previous(user)
    elif request_action == 'next':
        next(user)
    
    print('AFTER: ' + request_action + ' FOR @' + str(user.username))

def play(user, room, offset = None):
    data = {}

    if offset is not None:
        data['context_uri'] = 'spotify:playlist:' + str(room.playlist_id)
        data['offset'] = {
            'position': offset
        }

    put(user, play_endpoint, data = data)

def play_direct(user, room, action_data):
    offset = action_data['offset']

    room.playlist.song_index = offset
    room.playlist.progress_ms = 0
    room.playlist.save()

    play(user, room, offset = offset)

def pause(user, room):
    position_ms = room.playlist.progress_ms

    put(user, pause_endpoint)
    time.sleep(.1)
    seek(user, {
        'seek_ms': position_ms
    })

def seek(user, action_data):
    params = {
        'position_ms': action_data['seek_ms']
    }

    put(user, seek_endpoint, params = params)

def previous(user):
    post(user, previous_endpoint)

def next(user):
    post(user, next_endpoint)

def get_progress(room):
    position_ms = room.playlist.progress_ms
    difference = round((timezone.now() - room.playlist.last_action).total_seconds() * 1000)
    progress_ms = position_ms + difference

    return progress_ms

def refresh_token(user):
    response = requests.post(refresh_endpoint, data = {
        'grant_type': 'refresh_token',
        'refresh_token': user.userprofile.refresh_token
    }, headers = get_token_headers())

    r_json = response.json()

    if response.status_code < 400:
        user.userprofile.access_token = r_json['access_token']
        user.userprofile.authorized = True
    else:
        user.userprofile.authorized = False
    
    user.userprofile.save()

    return user.userprofile.authorized

def get_playlist_data(user, playlist_id):
    playlist_data = get(user, playlist_endpoint + playlist_id)

    return playlist_data.json()

def get_song_data(user):
    song_data = get(user, song_endpoint)

    return song_data.json()

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

def get(user, endpoint):
    response = requests.get(endpoint, headers = get_headers(user))

    if response.status_code == 401:
        authorized = refresh_token(user)

        if authorized:
            response = requests.get(endpoint, headers=get_headers(user))

    return response

def put(user, endpoint, data = {}, params = {}):
    data = json.dumps(data)

    response = requests.put(endpoint, params = params, data = data, headers = get_headers(user))

    if response.status_code == 401:
        authorized = refresh_token(user)

        if authorized:
            response = requests.put(endpoint, params = data, headers = get_headers(user))

    return response

def post(user, endpoint, data = {}):
    data = json.dumps(data)

    response = requests.post(endpoint, data = data, headers = get_headers(user))

    if response.status_code == 401:
        authorized = refresh_token(user)

        if authorized:
            response = requests.post(endpoint, data = data, headers = get_headers(user))
        else:
            response = {
                'error': 'unauthorized',
                'error_message': 'User is unauthorized'
            }

    return response