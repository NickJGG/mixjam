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
    playlist_notifications = ['song_end']

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
                            'username': user.username,
                            'color': user.userprofile.background_color,
                            'profile_picture': render_to_string('core/blocks/profile-picture.html', {
                                'width': 'var(--user-width)',
                                'height': 'var(--user-width)',
                                'user': user
                            }),
                        }
                    }
                }
            }
        )

        await self.request_playlist({
            'data': {
                'action': 'get_state'
            }
        })

        #await spotify.update_play(user, room)

    # DISCONNECT FUNCTION
    async def disconnect(self, close_code):
        await self.offline()

        await self.channel_layer.group_send(
            self.group_name,
            {
                'type': 'request_connection',
                'data': {
                    'connection_state': {
                        'connection_type': 'leave',
                        'user': self.scope['user'].username
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

        if 'type' not in request_data or 'data' not in request_data:
            pass

        if request_data['type'] == 'playlist' and request_data['data']['action'] not in self.playlist_notifications:
            spotify.update_playlist(self.scope['user'], self.get_room(), request_data['data'])
        elif request_data['type'] == 'chat':
            user = self.scope['user']

            request_data['data']['action_data']['user'] = {
                'username': user.username,
                'color': user.userprofile.background_color
            }

        self.print_request(request_data)

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

        if request_action not in self.playlist_notifications:
            await spotify.action(user, room, request_action, request_action_data)

            #if r.status_code not in range(200, 299):
                #return False
        elif request_action == 'song_end':
            await room.playlist.next_song()
            await spotify.sync(user, room)
    
        room_state = await util.get_room_state(user, room.code)

        await self.response_send('playlist', room_state)

    async def request_chat(self, request_data):
        request_data['data']['action_data']['user']['self'] = request_data['data']['action_data']['user']['username'] == self.scope['user'].username

        await self.response_send('chat', request_data['data'])

    async def request_journey(self, request_data):
        pass

    async def request_connection(self, request_data):
        await self.response_send('connection', request_data)

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

    def get_room(self):
        room = Room.objects.filter(code=self.room_name)

        return room[0] if room.exists() else None
    
    def print_request(self, request_data):
        print('\n=== RECEIVED REQUEST ===============')
        print('Time: ' + datetime.now().strftime('%I:%M:%S %m/%d'))
        print('\nType: ' + request_data['type'])
        print('Data: ' + json.dumps(request_data['data'], indent = 4))
        print('==================== END REQUEST ===\n')