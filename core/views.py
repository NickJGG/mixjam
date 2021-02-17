from django.shortcuts import render, redirect
from django.utils.crypto import get_random_string
from django.contrib.auth import authenticate, login as auth_login

import spotify

from .models import *

from . import util

client_id = '8b817932e631474cb15f7e36edcfc53b'
client_secret = '6ef495db91bd4268b520f861117d39f9'

def index(request):
    spot = spotify.SpotifyAPI(client_id, client_secret, request.user, '')

    print(spot.pause())
    print(spot.play())

    return render(request, 'core/index.html')
def callback(request):
    if request.GET and 'code' in request.GET:
        spot = spotify.SpotifyAPI(client_id, client_secret, request.user, request.GET['code'])
        spot.perform_user_auth()

        print(request.user.userprofile.access_token)

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

    data['room'] = room
    data['room_state'] = util.get_room_state(request.user, room_code)

    return render(request, 'core/room.html', data)

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