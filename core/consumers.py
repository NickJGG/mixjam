from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncWebsocketConsumer

from .models import *
from . import util
from . import spotify

from datetime import datetime
from django.utils import timezone

import json
import requests
import time

class RoomConsumer(AsyncWebsocketConsumer):
    put_methods = ['play', 'pause']
    post_methods = ['previous', 'next']

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
                        'user': user.username
                    }
                }
            }
        )

        #spotify.update_play(user, room)

        await self.request_playlist({
            'data': {
                'action': 'get_state'
            }
        })

    # DISCONNECT FUNCTION
    async def disconnect(self, close_code):
        await self.channel_layer.group_send(
            self.group_name,
            {
                'action': 'connection',
                'success': True,
                'connection_state': {
                    'connection_type': 'leave',
                    'user': self.scope['user'].username
                },
                'type': 'room_send',
            }
        )

        await self.channel_layer.group_discard(
            self.group_name,
            self.channel_name
        )

        await self.offline()

    # HELPER FUNCTIONS

    @database_sync_to_async
    def online(self):
        room = self.get_room()

        if request_data['type'] == 'request_playlist':
            spotify.playlist_control(self.scope['user'], self.get_room(), request_data['data'])

        await self.channel_layer.group_send(
            self.group_name, request_data
        )

    @database_sync_to_async
    def offline(self):
        room = self.get_room()

    async def request_playlist(self, request_data):
        request_data = request_data['data']

        request_action = request_data['action']
        request_action_data = request_data['action_data'] if 'action_data' in request_data else None

    @database_sync_to_async
    def music_control(self, data):
        print('MUSIC CONTROL')

        action = data['action']
        offset = data['offset'] if 'offset' in data else None

        user = self.scope['user']

            spotify.action(user, self.get_room(), request_action, request_action_data)

            #if r.status_code not in range(200, 299):
                #return False

            time.sleep(.2)
    
        await self.response_send('playlist', util.get_room_state(user, self.get_room().code))

    def base_control(self, username, option, offset = None):
        endpoint = spotify.player_endpoint + option

        user = User.objects.filter(username = username)

        if user.exists():
            user = user[0]

            data = {}

    @database_sync_to_async
    def online(self):
        user = self.scope['user']
        room = self.get_room()

        if room:
            room.active_users.add(user)

            if option in self.put_methods:
                r = spotify.put(user, endpoint, data = data)
            elif option in self.post_methods:
                r = spotify.post(user, endpoint, data = data)

            if r.status_code not in range(200, 299):
                return False

            return True

        return False