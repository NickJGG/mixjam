import os

from urllib.parse import urlunsplit, urlencode

from django import template

from channels.layers import get_channel_layer

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

@register.simple_tag
def get_action_info(inviter, invitee, room):
    active = room.active_users.filter(username = invitee.username).exists()
    in_room = room.users.filter(username = invitee.username).exists()
    is_leader = inviter == room.leader

    can_invite = not active and (room.leader == inviter or room.mode != RoomMode.CLOSED or in_room)

    print('\nINVITER: ', inviter, '\nINVITEE: ', invitee, '\nACTIVE: ', active, '\nIN ROOM: ', in_room, '\nCAN INVITE: ', can_invite, '\nIS LEADER: ', is_leader, '\n')
    print(inviter, room.leader)

    return {
        'active': active,
        'in_room': in_room,
        'can_invite': can_invite,
        'is_leader': is_leader
    }

@register.simple_tag
def get_playlist_url(id):
    return 'https://open.spotify.com/playlist/' + id
    
@register.simple_tag
def is_friend(user, other_user):
    return user.userprofile.friends.filter(username = other_user.username).exists()