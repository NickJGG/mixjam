import json
import requests
import time

from datetime import datetime

from django.utils import timezone
from django.template.loader import render_to_string

from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncWebsocketConsumer

from .models import *
from . import util
from . import spotify

class RoomConsumer(AsyncWebsocketConsumer):
    put_methods = ['play', 'pause', 'seek']
    post_methods = ['previous', 'next']
    playlist_notifications = []

    playlist_to_notif = {
        'play': 'resumed play',
        'play_direct': 'played',
        'pause': 'paused play',
        'previous': 'skipped back to',
        'next': 'skipped to',
        'seek': 'seeked to',
    }

    # CONNECT FUNCTION
    async def connect(self):
        room_code = self.scope['url_route']['kwargs']['room_code']
        user = self.scope['user']
        room = Room.objects.get(code = room_code)

        self.room_name = room_code
        self.group_name = 'room_%s' % self.room_name

        await self.channel_layer.group_add(
            self.group_name,
            self.channel_name
        )

        await self.online()

        await self.accept()

        await self.channel_layer.group_send(
            self.group_name,
            {
                'type': 'request_connection',
                'data': {
                    'connection_state': {
                        'connection_type': 'join',
                        'user': {
                            'username': user.username
                        }
                    }
                }
            }
        )

        await spotify.update_play(user, room)

        await self.request_playlist({
            'data': {
                'action': 'get_state'
            }
        })

        await self.send_notification('join', user, 'joined', before_subject = render_to_string('core/blocks/profile-picture.html', {
            'width': '20px',
            'height': '20px',
            'user': user
        }))

    # DISCONNECT FUNCTION
    async def disconnect(self, close_code):
        await self.offline()

        user = self.scope['user']
        room = self.get_room()

        await self.send_notification('leave', user, 'left', before_subject = render_to_string('core/blocks/profile-picture.html', {
            'width': '20px',
            'height': '20px',
            'user': user
        }))

        if user in room.users.all():
            await self.channel_layer.group_send(
                self.group_name,
                {
                    'type': 'request_connection',
                    'data': {
                        'connection_state': {
                            'connection_type': 'leave',
                            'user': {
                                'username': user.username
                            }
                        }
                    }
                }
            )

        await self.channel_layer.group_discard(
            self.group_name,
            self.channel_name
        )

    # RECEIVE FUNCTION (WILL CALL FOR USER)
    async def receive(self, text_data):
        request_data = json.loads(text_data)

        request_type = request_data['type']
        request_action = request_data['data']['action']

        user = self.scope['user']
        room = self.get_room()

        self.print_request(request_data)

        if request_type == 'playlist' and request_action not in self.playlist_notifications:
            spotify.update_playlist(user, room, request_data['data'])

            request_data['data']['action_data']['user'] = user
        elif request_data['type'] == 'chat':
            request_data['data']['action_data']['user'] = {
                'username': user.username,
                'color': user.userprofile.background_color
            }
        elif request_type == 'admin':
            if request_action == 'kick':
                if user == room.leader:
                    kicked_user = User.objects.get(username = request_data['data']['action_data']['user'])

                    request_data['data']['successful'] = True

                    await util.kick(room, kicked_user)
                else:
                    request_data['data']['successful'] = False
        elif request_type == 'user_action':
            if request_action == 'profile':
                profile_user = User.objects.get(username = request_data['data']['action_data']['user'])

                block = render_to_string('core/blocks/user-card.html', {
                    'user': profile_user
                })

                request_data['data']['block'] = block

                await self.send(text_data=json.dumps({
                    'type': request_type,
                    'response_data': request_data['data']
                }))
            
                return
            elif request_action == 'leave':
                request_data['data']['action_data']['user'] = user.username

        request_data['type'] = 'request_' + request_data['type']

        await self.channel_layer.group_send(
            self.group_name, request_data
        )

    async def response_send(self, type, response_data):
        await self.send(text_data=json.dumps({
            'type': type,
            'response_data': response_data
        }))

    async def request_playlist(self, request_data):
        request_data = request_data['data']

        request_action = request_data['action']
        request_action_data = request_data['action_data'] if 'action_data' in request_data else None

        user = self.scope['user']
        room = self.get_room()

        method_data = {}
        method_params = {}

        before_subject = None
        before_object = None

        if request_action not in self.playlist_notifications:
            await spotify.action(user, room, request_action, request_action_data)

            if request_action in self.playlist_to_notif.keys():
                before_subject = render_to_string('core/blocks/profile-picture.html', {
                    'width': '20px',
                    'height': '20px',
                    'user': request_action_data['user']
                })
    
        room_state = await spotify.get_room_state(user, room.code)

        await self.response_send('playlist', room_state)

        if before_subject is not None:
            await self.send_notification_self(request_action, request_action_data['user'].username, self.playlist_to_notif[request_action], before_subject = before_subject, before_object = before_object)

    async def request_chat(self, request_data):
        request_data['data']['action_data']['user']['self'] = request_data['data']['action_data']['user']['username'] == self.scope['user'].username

        await self.response_send('chat', request_data['data'])

    async def request_admin(self, request_data):
        request_data = request_data['data']

        request_action = request_data['action']
        request_action_data = request_data['action_data'] if 'action_data' in request_data else None

        user = self.scope['user']
        room = self.get_room()
        
        if request_action == 'kick':
            if request_data['successful']:
                if user.username == request_action_data['user']:
                    await self.response_send('admin', request_data)
                else:
                    await self.channel_layer.group_send(
                        self.group_name,
                        {
                            'type': 'request_connection',
                            'data': {
                                'connection_state': {
                                    'connection_type': 'kick',
                                    'user': {
                                        'username': request_action_data['user']
                                    }
                                }
                            }
                        }
                    )

                    await self.send_notification(request_action, room.leader, 'kicked', request_action_data['user'], before_subject = render_to_string('core/blocks/profile-picture.html', {
                        'width': '20px',
                        'height': '20px',
                        'user': room.leader
                    }), before_object = render_to_string('core/blocks/profile-picture.html', {
                        'width': '20px',
                        'height': '20px',
                        'user': User.objects.get(username = request_action_data['user'])
                    }))
        elif request_action == 'delete':
            await self.response_send('admin', request_data)

    async def request_notification(self, request_data):
        await self.response_send('notification', request_data)

    async def request_user_action(self, request_data):
        request_data = request_data['data']

        await self.response_send('user_action', request_data)

    async def request_connection(self, request_data):
        if request_data['data']['connection_state']['connection_type'] != 'kick':
            user = self.scope['user']
            room = self.get_room()

            connection_user = User.objects.get(username = request_data['data']['connection_state']['user']['username'])

            request_data['data']['connection_state']['user']['user_block'] = render_to_string('core/blocks/room/user.html', {
                'user': connection_user,
                'request_user': user,
                'is_leader': connection_user == room.leader,
                'show_admin': user == room.leader
            })

        await self.response_send('connection', request_data)

    async def send_notification(self, request_action, subject, action, object = None, before_subject = None, before_object = None):
        block_data = {
            'subject': subject,
            'action': action,
            'object': object,
            'before_subject': before_subject,
            'before_object': before_object
        }

        await self.channel_layer.group_send(
            self.group_name,
            {
                'type': 'request_notification',
                'data': {
                    'request_action': request_action,
                    'block': render_to_string('core/blocks/room/notification.html', block_data)
                }
            }
        )

    async def send_notification_self(self, request_action, subject, action, object = None, before_subject = None, before_object = None):
        block_data = {
            'subject': subject,
            'action': action,
            'object': object,
            'before_subject': before_subject,
            'before_object': before_object
        }

        await self.response_send('request_notification', {
            'data': {
                'request_action': request_action,
                'block': render_to_string('core/blocks/room/notification.html', block_data)
            }
        })

    # HELPER FUNCTIONS

    @database_sync_to_async
    def online(self):
        room = self.get_room()

        if room:
            room.active_users.add(self.scope['user'])

    @database_sync_to_async
    def offline(self):
        room = self.get_room()

        if room:
            room.active_users.remove(self.scope['user'])
            room.save()

            if not room.is_active():
                if room.playlist.playing:
                    room.playlist.progress_ms = util.get_adjusted_progress(room)
                    room.playlist.playing = False
                    room.playlist.save()

    def get_room(self):
        room = Room.objects.filter(code=self.room_name)

        return room[0] if room.exists() else None
    
    def print_request(self, request_data):
        print('\n=== RECEIVED REQUEST ===============')
        print('Time: ' + datetime.now().strftime('%I:%M:%S %m/%d'))
        print('User: ' + self.scope['user'].username)
        print('\nType: ' + request_data['type'])
        print('Data: ' + json.dumps(request_data['data'], indent = 4))
        print('==================== END REQUEST ===\n')