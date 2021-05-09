import os
import base64
import json
import requests
import time
import math

from channels.db import database_sync_to_async

import requests_async

from django.utils import timezone

from .models import *
from . import util

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

        room.playlist.progress_ms = util.get_adjusted_progress(room)
    elif action == 'play_direct' or action == 'previous' or action == 'next':
        room.playlist.progress_ms = 0
        room.playlist.playing = True
        
        if action == 'previous':
            room.playlist.previous_song()
        elif action == 'next':
            room.playlist.next_song()
        else:
            room.playlist.song_index = action_data['offset']
            room.playlist.progress_ms = 0
    elif action == 'seek':
        room.playlist.progress_ms = action_data['seek_ms']
    elif action == 'song_end':
        room.playlist.song_end()
    
    room.playlist.last_action = timezone.now()
    room.playlist.save()

    print('""""" PLAYLIST UPDATE """""')
    print('PLAYING: ' + str(room.playlist.playing))
    print('SONG INDEX: ' + str(room.playlist.song_index))
    print('PROGRESS(MS): ' + str(room.playlist.progress_ms))
    print('LAST ACTION: ' + str(room.playlist.last_action))
    print('"""""""""""""""""""""""""""')

async def update_play(user, room):
    if room.others_active(user):
        progress_ms = room.playlist.get_progress(user)

        await play_direct(user, room, {
            'offset': room.playlist.song_index,
        })

async def action(user, room, request_action, action_data = None):
    before = timezone.now()

    print('BEFORE: ' + request_action + ' FOR @' + str(user.username) + ' at ' + str(before))

    if request_action == 'play':
        await play(user, room)
    elif request_action == 'play_direct':
        await play_direct(user, room, action_data)
    elif request_action == 'pause':
        await pause(user, room)
    elif request_action == 'seek':
        await seek(user, action_data)
    elif request_action == 'previous':
        await previous(user)
    elif request_action == 'next':
        await next(user)
    elif request_action == 'song_end':
        await sync(user, room)

    after = timezone.now()

    print('AFTER:  ' + request_action + ' FOR @' + str(user.username) + ' at ' + str(after))
    print('duration: ' + str((after - before).total_seconds()))

async def play(user, room, offset = None):
    data = {}

    if offset is not None:
        data['context_uri'] = 'spotify:playlist:' + str(room.playlist_id)
        data['offset'] = {
            'position': offset
        }

    await put(user, play_endpoint, data = data)

async def play_direct(user, room, action_data):
    await play(user, room, offset = action_data['offset'])
    await sync(user, room)

async def pause(user, room):
    await put(user, pause_endpoint)
    await sync(user, room)

async def sync(user, room, progress_ms = None):
    seek_ms = progress_ms if progress_ms is not None else room.playlist.get_progress(user)

    await seek(user, {
        'seek_ms': seek_ms
    })

async def seek(user, action_data):
    params = {
        'position_ms': action_data['seek_ms']
    }

    await put(user, seek_endpoint, params = params)

async def previous(user):
    await post(user, previous_endpoint)

async def next(user):
    await post(user, next_endpoint)

async def refresh_token(user):
    response = await requests_async.post(refresh_endpoint, data = {
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

async def get_playlist_data(user, playlist_id):
    playlist_data = (await get(user, playlist_endpoint + playlist_id)).json()

    if playlist_data['tracks']['total'] > 100:
        for x in range(math.floor(playlist_data['tracks']['total'] / 100)):
            tracks = (await get(user, playlist_endpoint + playlist_id + '/tracks', params = {
                'offset': (x + 1) * 100
            })).json()

            playlist_data['tracks']['items'].extend(tracks['items'])

    return playlist_data

async def get_room_state(user, room_code):
    room = Room.objects.get(code = room_code)

    playlist_state = (await get_playlist_state(user, room_code))
    
    print(type(playlist_state))

    if room.playlist.song_index >= len(playlist_state['tracks']['items']):
        await room.playlist.restart()

    song_state = playlist_state['tracks']['items'][room.playlist.song_index]

    song_state['is_playing'] = room.playlist.playing
    song_state['progress_ms'] = room.playlist.get_progress(user)

    return {
        'song_state': song_state,
        'playlist_state': playlist_state
    }

async def get_playlist_state(user, room_code):
    room = Room.objects.filter(code = room_code)

    if not room.exists() or room[0].playlist_id is None:
        return None

    room = room[0]

    playlist_data = await get_playlist_data(user, room.playlist_id)

    if room.playlist_image_url is None:
        await util.update_playlist_image(room, playlist_data['images'][0]['url'])

    return playlist_data

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

async def get(user, endpoint, params = {}):
    response = await requests_async.get(endpoint, params = params, headers = get_headers(user))

    print(params)

    if response.status_code == 401:
        authorized = await refresh_token(user)

        if authorized:
            response = await requests_async.get(endpoint, params = params, headers=get_headers(user))

    return response

async def put(user, endpoint, data = {}, params = {}):
    data = json.dumps(data)

    response = await requests_async.put(endpoint, params = params, data = data, headers = get_headers(user))

    if response.status_code == 401:
        authorized = await refresh_token(user)

        if authorized:
            response = requests_async.put(endpoint, params = data, headers = get_headers(user))

    return response

async def post(user, endpoint, data = {}):
    data = json.dumps(data)

    response = await requests_async.post(endpoint, data = data, headers = get_headers(user))

    if response.status_code == 401:
        authorized = await refresh_token(user)

        if authorized:
            response = requests_async.post(endpoint, data = data, headers = get_headers(user))
        else:
            response = {
                'error': 'unauthorized',
                'error_message': 'User is unauthorized'
            }

    return response