import os
import random

from django.core.mail import send_mail, BadHeaderError
from django.db.models.query_utils import Q
from django.http import HttpResponse
from django.shortcuts import render, redirect
from django.utils.crypto import get_random_string
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from django.contrib.auth import authenticate, login as auth_login, logout as auth_logout, update_session_auth_hash
from django.contrib.auth.forms import PasswordResetForm
from django.contrib.auth.tokens import default_token_generator
from django.contrib import messages
from django.templatetags.static import static
from django.template.loader import render_to_string

from channels.db import database_sync_to_async

import spotify as spotify_auth
from syncify import settings

from .models import *

from . import util, spotify

client_id = os.environ.get('CLIENT_ID')
client_secret = os.environ.get('CLIENT_SECRET')

errors = {
    'no_link': {
        'error_title': 'Spotify Link Error',
        'error_message': 'No Spotify account linked',
        'error_code': 100
    },
    'non_member': {
        'error_title': 'Room Error',
        'error_message': 'You are not a member of this room',
        'error_code': 101
    },
    'invalid_invite': {
        'error_title': 'Invite Error',
        'error_message': 'Invite code invalid',
        'error_code': 102
    },
    'expired_invite': {
        'error_title': 'Invite Error',
        'error_message': 'Invite code expired',
        'error_code': 103
    },
    'invalid_room': {
        'error_title': 'Invite Error',
        'error_message': 'Room does not exist',
        'error_code': 104
    }
}

def index(request):
    if request.user.is_authenticated:
        return home(request)
    else:
        return landing(request)

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

    response = spotify.get(request.user, spotify.endpoints['current_user_playlists'])

    if request.user.userprofile.authorized:
        playlists = response.json()['items']
    else:
        return render(request, 'core/error.html', errors['no_link'])

    if request.user.userprofile.new_user:
        new_user = True

        request.user.userprofile.new_user = False
        request.user.userprofile.save()
    else:
        new_user = False

    return render(request, 'core/home.html', {
        'other_rooms': rooms,
        'playlists': playlists,
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

def room(request, room_code):
    data = {}

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

        if request.user not in room.users.all():
            if room.mode == RoomMode.PUBLIC:
                room.users.add(request.user)
                room.inactive_users.add(request.user)
                room.save()
            else:
                return render(request, 'core/error.html', errors['non_member'])

        request.user.userprofile.most_recent_room = room
        request.user.userprofile.save()

        room.check_invite()

        offline_users = []

        for user in room.users.all():
            if user not in room.active_users.all():
                offline_users.append(user)

        new_room = request.user in room.inactive_users.all()

        if new_room:
            room.inactive_users.remove(request.user)
            room.save()

        data['room'] = room
        data['new_room'] = new_room
        data['offline_users'] = offline_users
    else:
        return render(request, 'core/error.html', errors['invalid_room'])

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
            return render(request, 'core/error.html', errors['expired_invite'])
    else:
        return render(request, 'core/error.html', errors['invalid_invite'])

def account(request):
    path = os.path.join(settings.BASE_DIR, 'core', 'static', 'img', 'profile')
    file_list = os.listdir(path)

    if request.POST:
        if 'panel-label' in request.POST:
            panel = request.POST.get('panel-label')

            changed = False

            if panel == 'personalization':
                icon_image = request.POST.get('icon-image')
                icon_color = request.POST.get('icon-color')
                background_color = request.POST.get('background-color')

                if icon_image:
                    if not changed and icon_image != request.user.userprofile.icon_image:
                        changed = True

                        request.user.userprofile.icon_image = icon_image

                if icon_color:
                    try:
                        int(icon_color, 16)
                        
                        if len(icon_color) > 6:
                            raise ValueError

                        if not changed and icon_color != request.user.userprofile.icon_color:
                            changed = True

                        request.user.userprofile.icon_color = icon_color
                    except:
                        messages.error(request, 'Icon color is in the wrong format (Hex)')
                
                if background_color:
                    try:
                        int(background_color, 16)

                        if len(background_color) > 6:
                            raise ValueError

                        if not changed and background_color != request.user.userprofile.background_color:
                            changed = True

                        request.user.userprofile.background_color = background_color
                    except:
                        messages.error(request, 'Background color is in the wrong format (Hex)')

                if changed:
                    messages.success(request, 'Details updated')

                request.user.userprofile.save()
            elif panel == 'overview':
                first_name = request.POST.get('first-name')
                last_name = request.POST.get('last-name')
                email = request.POST.get('email')
                tag_line = request.POST.get('tag-line')

                if first_name and len(first_name) > 0:
                    if not changed and first_name != request.user.first_name:
                        changed = True

                    request.user.first_name = first_name
                else:
                    messages.error(request, 'First name is too short')
                
                if last_name and len(last_name) > 0:
                    if not changed and last_name != request.user.last_name:
                        changed = True

                    request.user.last_name = last_name
                else:
                    messages.error(request, 'Last name is too short')

                if email and len(email) > 0:
                    if not changed and email != request.user.email:
                        changed = True

                    request.user.email = email
                else:
                    messages.error(request, 'Email is too short')
                
                if tag_line and len(tag_line) > 0:
                    if not changed and tag_line != request.user.userprofile.tag_line:
                        changed = True

                    request.user.userprofile.tag_line = tag_line
                else:
                    messages.error(request, 'Tag line is too short')

                request.user.userprofile.save()
                request.user.save()

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

def ssl_validation(request):
    return redirect(to=static('8A3D973566FBB24256364C68D5B03A1F.txt'))