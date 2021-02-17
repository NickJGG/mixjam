from django.shortcuts import render
from django.utils.crypto import get_random_string

import spotify

from .models import *

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
    rooms = Room.objects.filter(code = room_code)

    if rooms.exists():
        room = Room.objects.get(code = room_code)
    else:
        while True:
            new_code = get_random_string(length=6)

            rooms = Room.objects.filter(code = room_code)

            if not rooms.exists():
                break

        room = Room(code = new_code, leader = request.user)
        room.save()

    return render(request, 'core/room.html', {
        'room': room
    })

def play(request):
    spot = spotify.SpotifyAPI(client_id, client_secret, request.user, '')

    print(spot.play())

    return render(request, 'core/index.html')

def pause(request):
    spot = spotify.SpotifyAPI(client_id, client_secret, request.user, '')

    print(spot.pause())

    return render(request, 'core/index.html')