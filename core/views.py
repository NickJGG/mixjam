import os

from django.shortcuts import render, reverse, redirect
from django.utils.crypto import get_random_string
from django.contrib.auth import authenticate, login as auth_login, logout as auth_logout

from channels.db import database_sync_to_async

import spotify as spotify_auth
from syncify import settings

from .models import *

from . import util, spotify

client_id = os.environ.get('CLIENT_ID')
client_secret = os.environ.get('CLIENT_SECRET')

def index(request):
    if request.user.is_authenticated:
        return home(request)
    else:
        return landing(request)

def home(request):
    if request.POST:
        print(request.POST)

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

            room.playlist = Playlist(room = room)
            room.playlist.save()

            room.new_invite()
            room.save()

    response = spotify.get(request.user, spotify.endpoints['current_user_playlists'])

    for playlist in response.json()['items']:
        print(playlist['name'])

    return render(request, 'core/home.html', {
        'rooms': Room.objects.filter(users = request.user),
        'playlists': response.json()['items']
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

    return index(request)

def room(request, room_code):
    data = {}

    rooms = Room.objects.filter(code = room_code)

    print(rooms[0].banner_color)

    if rooms.exists():
        room = rooms[0]

        if request.POST:
            print(request.POST)

            section = request.POST.get('section')

            if section == 'appearance':
                banner_color = request.POST.get('banner-color')

                try:
                    int(banner_color, 16)

                    room.banner_color = banner_color
                    room.save()
                except:
                    pass
            elif section == 'privacy':
                if request.user == room.leader:
                    mode = request.POST.get('mode')
                    new_code = request.POST.get('new-code')

                    if new_code is not None:
                        room.new_invite()

                    room.mode = mode
                    room.save()

        if request.user not in room.users.all():
            if room.mode == RoomMode.PUBLIC:
                room.users.add(request.user)
                room.save()
            else:
                return render(request, 'core/error.html', {
                    'error_message': 'You are not a member of this room'
                })

        request.user.userprofile.most_recent_room = room
        request.user.userprofile.save()

        room.check_invite()

        offline_users = []

        for user in room.users.all():
            if user not in room.active_users.all():
                offline_users.append(user)

        data['room'] = room
        data['offline_users'] = offline_users
    else:
        return render(request, 'core/error.html', {
            'error_message': 'Room does not exist'
        })

    return render(request, 'core/room.html', data)

def invite(request, invite_code):
    room = Room.objects.filter(invite_code = invite_code)

    if room.exists():
        room = room[0]

        if room.check_invite():
            room.users.add(request.user)
            room.save()

            return redirect('room', room_code = room.code)
        else:
            return render(request, 'core/error.html', {
                'error_message': 'Invite code expired'
            })
    else:
        return render(request, 'core/error.html', {
            'error_message': 'Invite code either invalid or expired'
        })

def account(request):
    path = os.path.join(settings.BASE_DIR, 'core', 'static', 'img', 'profile')
    file_list = os.listdir(path)

    if request.POST:
        print(request.POST)

        if 'panel-label' in request.POST:
            panel = request.POST.get('panel-label')

            if panel == 'personalization':
                icon_image = request.POST.get('icon-image')
                icon_color = request.POST.get('icon-color')
                background_color = request.POST.get('background-color')

                try:
                    int(icon_color, 16)

                    request.user.userprofile.icon_image = icon_image
                    request.user.userprofile.icon_color = icon_color
                    request.user.userprofile.background_color = background_color
                    request.user.userprofile.save()
                except:
                    pass
            elif panel == 'overview':
                first_name = request.POST.get('first-name')
                last_name = request.POST.get('last-name')
                email = request.POST.get('email')
                tag_line = request.POST.get('tag-line')

                if first_name and last_name and email and tag_line:
                    request.user.first_name = first_name
                    request.user.last_name = last_name
                    request.user.email = email
                    request.user.userprofile.tag_line = tag_line

                    request.user.userprofile.save()
                    request.user.save()

    authorized = spotify.refresh_token(request.user)

    return render(request, 'core/account.html', {
        'images': file_list,
        'authorized': authorized
    })

def login(request):
    if request.POST:
        print(request.POST)

        username = request.POST.get('username')
        password = request.POST.get('password')

        user = authenticate(username = username, password = password)

        print(user)

        if user is not None:
            auth_login(request, user)

            return redirect('index')

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

        if password == confirm_password:
            user = User.objects.create_user(username, email, password)
            auth_login(request, user)

            userprofile = UserProfile(user = user)
            userprofile.save()

            return redirect('index')

    return render(request, 'core/register.html')