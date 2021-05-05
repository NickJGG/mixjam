from .models import *

from . import spotify

from django.utils import timezone

def get_room_state(user, room_code):
    room = Room.objects.filter(code = room_code)

    if room.exists():
        room = room[0]

    return {
        'song_state': get_song_state(user),
        'playlist_state': get_playlist_state(user, room_code)
    }

def get_song_state(user):
    song_data = spotify.get_song_data(user)

    return song_data

def get_playlist_state(user, room_code):
    room = Room.objects.filter(code = room_code)

    if not room.exists() or room[0].playlist_id is None:
        return None

    room = room[0]

    playlist_data = spotify.get_playlist_data(user, room.playlist_id)

    return playlist_data