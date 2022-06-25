from channels.db import database_sync_to_async

from django.utils import timezone

def get_adjusted_progress(room):
    position_ms = room.playlist.progress_ms if room.playlist.progress_ms else 0
    difference = round((timezone.now() - room.playlist.last_action).total_seconds() * 1000)
    progress_ms = position_ms + difference

    return progress_ms

@database_sync_to_async
def update_playlist_image(room, url):
    room.playlist_image_url = url
    room.save()

@database_sync_to_async
def kick(room, kicked_user):
    room.users.remove(kicked_user)
    room.save()