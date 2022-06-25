import os

from django.core.mail import send_mail, BadHeaderError
from django.core.exceptions import ValidationError
from django.db.models.query_utils import Q
from django.http import HttpResponse
from django.http.response import JsonResponse
from django.shortcuts import render, redirect
from django.utils.crypto import get_random_string
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from django.contrib.auth import authenticate, login as auth_login, logout as auth_logout, update_session_auth_hash
from django.contrib.auth.password_validation import validate_password
from django.contrib.auth.forms import PasswordResetForm
from django.contrib.auth.tokens import default_token_generator
from django.contrib.auth.decorators import user_passes_test
from django.contrib import messages
from django.templatetags.static import static
from django.template.loader import render_to_string
from django.forms import ModelForm

from channels.layers import get_channel_layer

from asgiref.sync import async_to_sync

import spotify as spotify_auth
from syncify import settings

from .models import *
from .decorators import *

from . import errors

from . import spotify
from .templatetags import util

client_id = os.environ.get('CLIENT_ID')
client_secret = os.environ.get('CLIENT_SECRET')

def index(request):
    if request.user.is_authenticated:
        return home(request)
    else:
        return landing(request)

@authorization_required
def home(request):
    if request.POST:
        name = request.POST.get('room-name')
        description = request.POST.get('room-description')
        id = request.POST.get('room-id')

        if name and description and id:
            while True:
                new_code = get_random_string(length=6)

                rooms = Room.objects.filter(code = new_code)

                if not rooms.exists():
                    break
            
            room = Room(code = new_code, title = name, description = description, leader = request.user, playlist_id = id)
            room.save()

            room.users.add(request.user)
            room.inactive_users.add(request.user)

            room.playlist = Playlist(room = room)
            room.playlist.save()

            response = spotify.get(request.user, spotify.endpoints['playlist'] + id)

            try:
                room.playlist_image_url = response.json()['images'][0]['url']
            except:
                pass

            room.new_invite()
            room.save()

            return redirect('room', room_code = room.code)

    rooms = Room.objects.filter(users = request.user).all()

    if request.user.userprofile.most_recent_room is not None: 
        if request.user not in request.user.userprofile.most_recent_room.users.all():
            request.user.userprofile.most_recent_room = None
            request.user.userprofile.save()
        else:
            rooms = [room for room in rooms if room.pk != request.user.userprofile.most_recent_room.pk]

    if request.user.userprofile.new_user:
        new_user = True

        request.user.userprofile.new_user = False
        request.user.userprofile.save()
    else:
        new_user = False

    return render(request, 'core/home.html', {
        'other_rooms': rooms,
        'recent_room': request.user.userprofile.most_recent_room if request.user.userprofile.most_recent_room is not None else None,
        'new_user': new_user
    })

def landing(request):
    return render(request, 'core/landing.html', {

    })

def callback(request):
    if request.GET and 'code' in request.GET:
        spot = spotify_auth.SpotifyAPI(client_id, client_secret, request.user, request.GET['code'])
        spot.perform_user_auth()

        request.user.userprofile.authorized = True
        request.user.userprofile.save()

        messages.success(request, 'Spotify account linked')

    return redirect('index')

def rooms(request):
    user_rooms = Room.objects.filter(users = request.user).all()

    return render(request, 'core/rooms.html', {
        'rooms': user_rooms,
    })

def announcements(request):
    announcements = Room.objects.filter(users = request.user).all()

    return render(request, 'core/announcements.html', {
        'announcements': announcements,
    })

@authorization_required
def room(request, room_code):
    data = {
        'in_room': True
    }

    rooms = Room.objects.filter(code = room_code)

    if rooms.exists():
        room = rooms[0]

        if request.POST:
            section = request.POST.get('section')

            if section == 'details':
                changed = False

                title = request.POST.get('name')
                description = request.POST.get('description')
                banner_color = request.POST.get('banner-color')

                if title and len(title) > 0:
                    if not changed and title != room.title:
                        changed = True

                    room.title = title
                else:
                    messages.error(request, 'Title is too short')
                
                if description and len(description) > 0:
                    if not changed and description != room.description:
                        changed = True

                    room.description = description
                else:
                    messages.error(request, 'Description is too short')

                try:
                    int(banner_color, 16)

                    if not changed and banner_color != room.banner_color:
                        changed = True

                    room.banner_color = banner_color
                except:
                    messages.error(request, 'Banner color is in the wrong format (Hex)')

                if changed:
                    messages.success(request, 'Details updated')

                room.save()
            elif section == 'privacy':
                if request.user == room.leader:
                    changed = False

                    mode = request.POST.get('mode')
                    new_code = request.POST.get('new-code')

                    if new_code is not None:
                        room.new_invite()

                        messages.success(request, 'New invite code generated')

                    if mode:
                        if not changed and mode != room.mode:
                            changed = True

                        room.mode = mode
                    
                    if changed:
                        messages.success(request, 'Privacy mode updated')

                    room.save()
            elif section == 'delete':
                room_name = room.title

                room.delete()

                messages.success(request, room_name + ' deleted')

                return redirect('index')
            elif section == 'leave':
                if request.user != room.leader:
                    room.users.remove(request.user)

                    request.session['visited-' + room.code] = False

                    messages.success(request, 'Left ' + room.title)

                    return redirect('index')
            elif section == 'preferences':
                default_panel = request.POST.get('default-panel')

                request.session[room.code]['default_panel'] = default_panel
                request.session.modified = True

        if not room.users.filter(username = request.user).exists():
            if room.mode == RoomMode.PUBLIC:
                room.users.add(request.user)
                room.inactive_users.add(request.user)
                room.save()
            else:
                return errors.non_member(request)

        request.user.userprofile.most_recent_room = room
        request.user.userprofile.save()

        room.check_invite()

        offline_users = []

        for user in room.users.all():
            if not room.active_users.filter(username = user).exists():
                offline_users.append(user)

        new_room = room.inactive_users.filter(username = request.user).exists()

        if new_room:
            room.inactive_users.remove(request.user)
            room.save()
        
        if room.code not in request.session:
            request.session[room.code] = {
                'default_panel': 'home'
            }

            request.session.modified = True

        data['room'] = room
        data['new_room'] = new_room
        data['offline_users'] = offline_users
        data['session_data'] = request.session.get(room.code)
    else:
        return errors.invalid_room(request)

    return render(request, 'core/room.html', data)

def invite(request, invite_code):
    room = Room.objects.filter(invite_code = invite_code)

    if room.exists():
        room = room[0]

        if room.check_invite():
            room.users.add(request.user)
            room.inactive_users.add(request.user)
            room.save()

            return redirect('room', room_code = room.code)
        else:
            return errors.expired_invite(request)
    else:
        return errors.invalid_invite(request)

def account(request):
    authorized = spotify.refresh_token(request.user)

    return render(request, 'core/account.html', {
        'authorized': authorized
    })

def account_edit(request):
    if request.POST:
        if 'panel-label' in request.POST:
            panel = request.POST.get('panel-label')

            changed = False

            if panel == 'personalization':
                color = request.POST.get('color')

                if 'small' in request.FILES:
                    if request.user.userprofile.picture is None:
                        new_picture = UserProfilePicture()
                        new_picture.save()
                        
                        request.user.userprofile.picture = new_picture

                    request.user.userprofile.picture.small = request.FILES.get('small')
                    request.user.userprofile.picture.medium = request.FILES.get('small')
                    request.user.userprofile.picture.large = request.FILES.get('small')
                    request.user.userprofile.picture.save()

                    changed = True

                if color:
                    try:
                        int(color, 16)

                        if len(color) > 6:
                            raise ValueError

                        request.user.userprofile.color = color

                        changed = True
                    except:
                        messages.error(request, 'Color is in the wrong format (Hex)')
                
                if changed:
                    messages.success(request, 'Profile updated')
                
                request.user.userprofile.save()
            elif panel == 'overview':
                form = UserForm(request.POST, instance = request.user)

                first_name = request.POST.get('first_name')
                last_name = request.POST.get('last_name')

                if first_name and len(first_name) > 0:
                    if last_name and len(last_name) > 0:
                        if form.is_valid():
                            form.save()

                            changed = True
                        else:
                            print(form.errors)
                    else:
                        messages.error(request, 'Last name is too short')
                else:
                    messages.error(request, 'First name is too short')

                form = ProfileForm(request.POST, instance = request.user.userprofile)

                if form.is_valid():
                    print('\n\n\nVALID\n\n\n')

                    form.save()

                    changed = True
                else:
                    print(form.errors)

                if changed:
                    messages.success(request, 'Details updated')
            elif panel == 'privacy':
                password1 = request.POST.get('password1')
                password2 = request.POST.get('password2')

                if password1 and password2:
                    if password1 == password2:
                        request.user.set_password(password1)
                        request.user.save()

                        update_session_auth_hash(request, request.user)

                        messages.success(request, 'Password changed')
                    else:
                        messages.error(request, 'Passwords do not match')
                else:
                    messages.error(request, 'Please enter a new password')
    
    return redirect('account')

class UserForm(ModelForm):
    class Meta:
        model = User
        fields = ('first_name', 'last_name', 'email')

class ProfileForm(ModelForm):
    class Meta:
        model = UserProfile
        fields = ('tag_line',)

class ImageForm(ModelForm):
    class Meta:
        model = UserProfilePicture
        fields = ('small', 'medium', 'large')

def notification(request):
    data = {
        'success': True
    }

    if request.POST:
        notification_id = request.POST.get('notification_id')
        accept = request.POST.get('accept') == 'true'

        notification = Notification.objects.filter(id = notification_id)

        if notification.exists():
            notification = notification[0]

            noti_type, noti = util.get_type_notification(notification)

            channel_layer = get_channel_layer()

            if noti_type == 'room_invite':
                if accept:
                    if not noti.room.users.filter(username = request.user.username).exists():
                        noti.room.inactive_users.add(request.user)
                    
                    noti.room.users.add(request.user)
                    noti.room.save()

                    async_to_sync(channel_layer.group_send)('user_' + notification.sender.username, {
                        'type': 'request_notification',
                        'data': {
                            'type': 'room_invite',
                            'notification_id': notification.id,
                            'notification_block': render_to_string('core/blocks/notification.html', {
                                'user': notification.receiver,
                                'message': 'accepted your room invite',
                                'type': 'user_action'
                            }),
                            'permanent': False
                        }
                    })
                    async_to_sync(channel_layer.group_send)('user_' + notification.receiver.username, {
                        'type': 'request_notification',
                        'data': {
                            'type': 'room_invite',
                            'notification_id': notification.id,
                            'notification_block': render_to_string('core/blocks/notification.html', {
                                'message': 'Joined room',
                                'type': 'text'
                            }),
                            'permanent': False,
                            'room_url': reverse('room', kwargs = { 'room_code': noti.room.code})
                        }
                    })
                else:
                    async_to_sync(channel_layer.group_send)('user_' + notification.sender.username, {
                        'type': 'request_notification',
                        'data': {
                            'type': 'room_invite',
                            'notification_id': notification.id,
                            'notification_block': render_to_string('core/blocks/notification.html', {
                                'user': notification.receiver,
                                'message': 'denied your room invite',
                                'type': 'user_action'
                            }),
                            'permanent': False
                        }
                    })
                    async_to_sync(channel_layer.group_send)('user_' + notification.receiver.username, {
                        'type': 'request_notification',
                        'data': {
                            'type': 'room_invite',
                            'notification_id': notification.id,
                            'notification_block': render_to_string('core/blocks/notification.html', {
                                'message': 'Room invite denied',
                                'type': 'text'
                            }),
                            'permanent': False
                        }
                    })

                notification.delete()
            elif noti_type == 'friend_request':
                if accept:
                    notification.sender.userprofile.friends.add(notification.receiver)
                    notification.receiver.userprofile.friends.add(notification.sender)

                    async_to_sync(channel_layer.group_send)('user_' + notification.sender.username, {
                        'type': 'request_notification',
                        'data': {
                            'type': 'friend_add',
                            'notification_id': notification.id,
                            'notification_block': render_to_string('core/blocks/notification.html', {
                                'user': notification.receiver,
                                'message': 'accepted your friend request',
                                'type': 'user_action'
                            }),
                            'friend_block': render_to_string('core/blocks/side-panel-items/friend.html', {
                                'friend': notification.receiver,
                                'user': notification.sender
                            }),
                            'friend_online': notification.receiver.userprofile.online_count > 0,
                            'permanent': False
                        }
                    })
                    async_to_sync(channel_layer.group_send)('user_' + notification.receiver.username, {
                        'type': 'request_notification',
                        'data': {
                            'type': 'friend_add',
                            'notification_id': notification.id,
                            'notification_block': render_to_string('core/blocks/notification.html', {
                                'user': notification.sender,
                                'message': 'is now your friend',
                                'type': 'user_action'
                            }),
                            'friend_block': render_to_string('core/blocks/side-panel-items/friend.html', {
                                'friend': notification.sender,
                                'user': notification.receiver
                            }),
                            'friend_online': notification.sender.userprofile.online_count > 0,
                            'permanent': False
                        }
                    })
                else:
                    async_to_sync(channel_layer.group_send)('user_' + notification.sender.username, {
                        'type': 'request_notification',
                        'data': {
                            'type': 'friend_request',
                            'notification_id': notification.id,
                            'notification_block': render_to_string('core/blocks/notification.html', {
                                'user': notification.receiver,
                                'message': 'denied your friend request',
                                'type': 'user_action'
                            }),
                            'permanent': False
                        }
                    })
                    async_to_sync(channel_layer.group_send)('user_' + notification.receiver.username, {
                        'type': 'request_notification',
                        'data': {
                            'type': 'friend_request',
                            'notification_id': notification.id,
                            'notification_block': render_to_string('core/blocks/notification.html', {
                                'message': 'Friend request denied',
                                'type': 'text'
                            }),
                            'permanent': False
                        }
                    })

                notification.delete()
        else:
            data['success'] = False

    return JsonResponse(data)

def request_friend(request):
    data = {
        'success': True
    }

    channel_layer = get_channel_layer()

    if request.GET:
        query = request.GET.get('query')

        target_user = User.objects.filter(username = query)

        if target_user.exists():
            target_user = target_user[0]

            if request.user.userprofile.friends.filter(id = target_user.id).exists():
                async_to_sync(channel_layer.group_send)('user_' + request.user.username, {
                    'type': 'request_notification',
                    'data': {
                        'type': 'friend_request',
                        'notification_block': render_to_string('core/blocks/notification.html', {
                            'message': 'User is already your friend',
                            'type': 'text'
                        }),
                        'permanent': False
                    }
                })
            elif FriendRequest.objects.filter(notification__sender = request.user, notification__receiver = target_user).exists():
                async_to_sync(channel_layer.group_send)('user_' + request.user.username, {
                    'type': 'request_notification',
                    'data': {
                        'type': 'friend_request',
                        'notification_block': render_to_string('core/blocks/notification.html', {
                            'message': 'Friend request already pending',
                            'type': 'text'
                        }),
                        'permanent': False
                    }
                })
            else:
                notification = Notification(sender = request.user, receiver = target_user)
                notification.save()

                friend_request = FriendRequest(notification = notification)
                friend_request.save()

                async_to_sync(channel_layer.group_send)('user_' + target_user.username, {
                    'type': 'request_notification',
                    'data': {
                        'type': 'friend_request',
                        'notification_block': render_to_string('core/blocks/notification.html', {
                            'noti': friend_request,
                            'message': 'wants to be friends',
                            'type': 'full'
                        }),
                        'permanent': True
                    }
                })

                async_to_sync(channel_layer.group_send)('user_' + request.user.username, {
                    'type': 'request_notification',
                    'data': {
                        'type': 'friend_request',
                        'notification_block': render_to_string('core/blocks/notification.html', {
                            'message': 'Friend request sent',
                            'type': 'text'
                        }),
                        'permanent': False
                    }
                })
        else:
            async_to_sync(channel_layer.group_send)('user_' + request.user.username, {
                'type': 'request_notification',
                'data': {
                    'type': 'friend_request',
                    'notification_block': render_to_string('core/blocks/notification.html', {
                        'message': 'User does not exist',
                        'type': 'text'
                    }),
                    'permanent': False
                }
            })

    return JsonResponse(data)

def remove_friend(request):
    data = {
        'success': True,
        'is_friend': True,
        'removed': True
    }

    if request.POST:
        username = request.POST.get('username')

        friend = request.user.userprofile.friends.filter(username = username)

        if friend.exists():
            friend = friend[0]

            request.user.userprofile.friends.remove(friend)
            friend.userprofile.friends.remove(request.user)

            channel_layer = get_channel_layer()

            async_to_sync(channel_layer.group_send)('user_' + friend.username, {
                'type': 'request_notification',
                'data': {
                    'type': 'friend_remove',
                    'notification_block': render_to_string('core/blocks/notification.html', {
                        'user': request.user,
                        'message': 'removed you as a friend',
                        'type': 'user_action',
                        'permanent': False
                    }),
                    'friend_username': request.user.username
                }
            })

            async_to_sync(channel_layer.group_send)('user_' + request.user.username, {
                'type': 'request_notification',
                'data': {
                    'type': 'friend_remove',
                    'notification_block': render_to_string('core/blocks/notification.html', {
                        'user': friend,
                        'message': 'removed as a friend',
                        'type': 'user_action',
                        'permanent': False
                    }),
                    'friend_username': friend.username
                }
            })
        else:
            data['is_friend'] = False
            data['removed'] = False
    else:
        data['success'] = False
    
    return JsonResponse(data)

def room_invite(request):
    if request.POST:
        username = request.POST.get('username')
        room_code = request.POST.get('room_code')

        friend = request.user.userprofile.friends.filter(username = username)
        room = Room.objects.get(code = room_code)

        if friend.exists():
            friend = friend[0]

            channel_layer = get_channel_layer()

            if room.active_users.filter(username = friend.username).exists():
                async_to_sync(channel_layer.group_send)('user_' + request.user.username, {
                    'type': 'request_notification',
                    'data': {
                        'type': 'room_invite',
                        'notification_block': render_to_string('core/blocks/notification.html', {
                            'message': 'User already in room',
                            'type': 'text',
                            'permanent': False
                        })
                    }
                })
            elif room.leader == request.user or room.mode != RoomMode.CLOSED:
                notification = Notification(sender = request.user, receiver = friend)
                notification.save()

                invite = RoomInvite(notification = notification, room = room)
                invite.save()

                async_to_sync(channel_layer.group_send)('user_' + friend.username, {
                    'type': 'request_notification',
                    'data': {
                        'type': 'room_invite',
                        'notification_block': render_to_string('core/blocks/notification.html', {
                            'noti': invite,
                            'message': 'wants you to join',
                            'type': 'room_invite'
                        }),
                        'permanent': True
                    }
                })

                async_to_sync(channel_layer.group_send)('user_' + request.user.username, {
                    'type': 'request_notification',
                    'data': {
                        'type': 'room_invite',
                        'notification_block': render_to_string('core/blocks/notification.html', {
                            'message': 'Room invite sent',
                            'type': 'text'
                        }),
                        'permanent': False
                    }
                })
    
    return JsonResponse({})

def room_kick(request):
    if request.POST:
        username = request.POST.get('username')
        room_code = request.POST.get('room_code')

        room = Room.objects.filter(code = room_code)

        if room.exists():
            room = room[0]

            user = User.objects.filter(username = username)

            if user.exists() and request.user == room.leader:
                channel_layer = get_channel_layer()

                async_to_sync(channel_layer.group_send)('room_' + room.code, {
                    'type': 'request_admin',
                    'data': {
                        'action': 'kick',
                        'action_data': {
                            'user': username
                        }
                    }
                })
    
    return JsonResponse({})

def login(request):
    if request.POST:
        username = request.POST.get('username')
        password = request.POST.get('password')

        user = authenticate(username = username, password = password)

        if user is not None:
            auth_login(request, user)

            return redirect('index')
        else:
            messages.error(request, 'Either username or password are invalid')

    return render(request, 'core/login.html')

def logout(request):
    auth_logout(request)

    return redirect('index')

def register(request):
    if request.POST:
        username = request.POST.get('username')
        email = request.POST.get('email')
        password = request.POST.get('password')
        confirm_password = request.POST.get('confirm-password')

        if not User.objects.filter(username = username).exists():
            if password == confirm_password:
                try:
                    validate_password(password)

                    user = User.objects.create_user(username, email, password)
                    auth_login(request, user)

                    userprofile = UserProfile(user = user)
                    userprofile.save()

                    return redirect('index')
                except ValidationError as error:
                    for e in error:
                        messages.error(request, e)
            else:
                messages.error(request, 'Passwords must match')
        else:
            messages.error(request, 'That username is already taken')

    return render(request, 'core/register.html')

def password_reset(request):
    if request.method == 'POST':
        password_reset_form = PasswordResetForm(request.POST)

        if password_reset_form.is_valid(): 
            data = password_reset_form.cleaned_data['email']
            associated_users = User.objects.filter(Q(email=data))
			
            if associated_users.exists():
                for user in associated_users:
                    subject = 'Password Reset Requested'
                    
                    c = {
                        'email': user.email,
                        'domain':'mixjam.io',
                        'site_name': 'MixJam',
                        'uid': urlsafe_base64_encode(force_bytes(user.pk)),
                        'user': user,
                        'token': default_token_generator.make_token(user),
                        'protocol': 'https',
				    }

                    email = render_to_string('core/password_reset/password_reset_email.txt', c)
					
                    try:
                        send_mail(subject, email, 'admin@mixjam.io' , [user.email], fail_silently=False)
                    except BadHeaderError:
                        return HttpResponse('Invalid header found.')
					
                    return redirect("password_reset_done")
            else:
                messages.error(request, 'The email you entered is not associated with any account')
    
    password_reset_form = PasswordResetForm()

    return render(request, 'core/password_reset/password_reset.html', {
        'password_reset_form': password_reset_form
    })

def test(request):
    return render(request, 'core/test.html')

def ssl_validation(request):
    return redirect(to=static('2C3B9EAF7A93B50467ACD8A6FB6C36AE.txt'))

from django.contrib.auth.decorators import user_passes_test