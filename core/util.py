from channels.db import database_sync_to_async

from .models import *

from . import spotify

async def get_room_state(user, room_code):
    room = Room.objects.get(code = room_code)

    playlist_state = await get_playlist_state(user, room_code)
    
    if room.playlist.song_index >= len(playlist_state['tracks']['items']):
        await room.playlist.restart()

    song_state = playlist_state['tracks']['items'][room.playlist.song_index]

    song_state['is_playing'] = room.playlist.playing
    song_state['progress_ms'] = room.playlist.progress_ms

    return {
        'song_state': song_state,
        'playlist_state': playlist_state
    }

def get_song_state(user):
    song_data = spotify.get_song_data(user)

    return song_data

async def get_playlist_state(user, room_code):
    room = Room.objects.filter(code = room_code)

    if not room.exists() or room[0].playlist_id is None:
        return None

    room = room[0]

    playlist_data = await spotify.get_playlist_data(user, room.playlist_id)

    if room.playlist_image_url is None:
        room.playlist_image_url = playlist_data['images'][1]['url']
        room.save()

    return playlist_data