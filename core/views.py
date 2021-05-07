import os

from django.shortcuts import render, redirect
from django.utils.crypto import get_random_string
from django.contrib.auth import authenticate, login as auth_login, logout as auth_logout

from channels.db import database_sync_to_async

import spotify
from syncify import settings
from urllib.parse import urlunsplit, urlencode

from .models import *

from . import util

client_id = os.environ.get('CLIENT_ID')
client_secret = os.environ.get('CLIENT_SECRET')
scheme = os.environ.get("API_SCHEME", "https")
netloc = os.environ.get("API_NETLOC", "accounts.spotify.com")

def index(request):
    if request.user.is_authenticated:
        return home(request)
    else:
        return landing(request)

def home(request):
    spot = spotify.SpotifyAPI(client_id, client_secret, request.user, '')

    redirect_uri = 'http://localhost:8000/callback/' if os.environ.get(
        'DJANGO_DEVELOPMENT') else 'http://syncified.herokuapp.com/callback/'

    path = f"/authorize"
    
    query = urlencode(dict(
        response_type = 'code',
        client_id = client_id,
        scope = 'streaming app-remote-control user-modify-playback-state user-read-currently-playing',
        redirect_uri = redirect_uri,
        state = 'null'
    ))

    authorize_url = urlunsplit((scheme, netloc, path, query, ""))

    print(authorize_url)

    return render(request, 'core/home.html', {
        'authorize_url': authorize_url
    })

def landing(request):
    return render(request, 'core/landing.html', {

    })

def callback(request):
    if request.GET and 'code' in request.GET:
        spot = spotify.SpotifyAPI(client_id, client_secret, request.user, request.GET['code'])
        spot.perform_user_auth()

    return render(request, 'core/callback.html')

def room(request, room_code):
    data = {}

    rooms = Room.objects.filter(code = room_code)

    if rooms.exists():
        room = rooms[0]
    else:
        '''while True:
            new_code = get_random_string(length=6)

            rooms = Room.objects.filter(code = room_code)

            if not rooms.exists():
                break

        room = Room(code = new_code, leader = request.user)
        room.save()'''

        room = Room(code = room_code, leader = request.user)
        room.save()

    if request.user not in room.users.all():
        room.users.add(request.user)
        room.save()

    if not Playlist.objects.filter(room = room).exists():
        room.playlist = Playlist(room = room)
        room.playlist.save()

    request.user.userprofile.most_recent_room = room
    request.user.userprofile.save()

    offline_users = []

    for user in room.users.all():
        if user not in room.active_users.all():
            offline_users.append(user)

    data['room'] = room
    data['offline_users'] = offline_users

    return render(request, 'core/room.html', data)

def account(request):
    print(settings.BASE_DIR)
    path = os.path.join(settings.BASE_DIR, 'core', 'static', 'img', 'profile')
    file_list = os.listdir(path)

    if request.POST:
        if 'panel-label' in request.POST:
            panel = request.POST.get('panel-label')

            if panel == 'personalization':
                icon_image = request.POST.get('icon-image')
                icon_color = request.POST.get('icon-color')
                background_color = request.POST.get('background-color')

                print(icon_color)

                try:
                    int(icon_color, 16)

                    print('is hex')

                    request.user.userprofile.icon_image = icon_image
                    request.user.userprofile.icon_color = icon_color
                    request.user.userprofile.background_color = background_color
                    request.user.userprofile.save()
                except:
                    print('is not hex')

    return render(request, 'core/account.html', {
        'images': file_list
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