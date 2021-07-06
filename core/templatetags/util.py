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
        'DJANGO_DEVELOPMENT') else 'https://mixjam.io/callback/'

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

@register.simple_tag
def get_friends_statuses(user):
    online = []
    offline = []

    for friend in user.userprofile.friends.all():
        if friend.userprofile.online_count > 0:
            online.append(friend)
        else:
            offline.append(friend)

    return {
        'online': online,
        'offline': offline
    }

@register.simple_tag
def get_notifications(user):
    model_notifications = Notification.objects.filter(receiver = user)

    notifications = []

    for noti in model_notifications:
        room_invite = RoomInvite.objects.filter(notification = noti)

        if room_invite.exists():
            room_invite = room_invite[0]

            room_invite.type = 'room_invite'
            room_invite.message = 'wants you to join'

            notifications.append(room_invite)
        else:
            friend_request = FriendRequest.objects.filter(notification = noti)

            if friend_request.exists():
                friend_request = friend_request[0]

                friend_request.type = 'friend_request'
                friend_request.message = 'wants to be friends'

                notifications.append(friend_request)
    
    return notifications

def get_type_notification(notification):
    room_invite = RoomInvite.objects.filter(notification = notification)

    if room_invite.exists():
        return 'room_invite', room_invite[0]
    else:
        friend_request = FriendRequest.objects.filter(notification = notification)

        if friend_request.exists():
            return 'friend_request', friend_request[0]

    return 'none', None

@register.simple_tag
def get_room_info(user):
    active_room = Room.objects.filter(active_users = user)

    if active_room.exists():
        return active_room[0]
    
    return None