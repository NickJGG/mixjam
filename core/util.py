from .models import *

from . import spotify

def get_room_state(user, room_code):
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

    if room.playlist_image_url is None:
        room.playlist_image_url = playlist_data['images'][1]['url']
        room.save()

    return playlist_data