import os

from urllib.parse import urlunsplit, urlencode

from django import template

from core.models import *

register = template.Library()

@register.simple_tag
def get_rooms(user):
    return Room.objects.filter(users = user).all()

@register.simple_tag
def get_room_count(user):
    return Room.objects.filter(users = user).count()

@register.simple_tag
def authorize_url():
    client_id = os.environ.get('CLIENT_ID')
    scheme = os.environ.get("API_SCHEME", "https")
    netloc = os.environ.get("API_NETLOC", "accounts.spotify.com")

    redirect_uri = 'http://localhost:8000/callback/' if os.environ.get(
        'DJANGO_DEVELOPMENT') else 'http://syncified.herokuapp.com/callback/'

    path = f"/authorize"

    query = urlencode(dict(
        response_type = 'code',
        client_id = client_id,
        scope = 'streaming app-remote-control user-modify-playback-state user-read-currently-playing playlist-read-private playlist-read-collaborative user-read-playback-state',
        redirect_uri = redirect_uri,
        state = 'null'
    ))

    return urlunsplit((scheme, netloc, path, query, ""))

@register.simple_tag
def is_leader(user, room):
    return user == room.leader