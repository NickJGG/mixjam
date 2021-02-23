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
        self.room_name = self.scope['url_route']['kwargs']['room_code']
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
                'action': 'connection',
                'success': True,
                'connection_state': {
                    'connection_type': 'join',
                    'user': self.scope['user'].username
                },
                'type': 'room_send',
            }
        )

    # SEND FUNCTIONS (WILL CALL FOR EVERYONE)
    async def room_send(self, event):
        data = {}

        items = list(event.items())

        for x in range(len(items)):
            key = items[x][0]
            value = items[x][1]

            if key == 'message_type':
                data['type'] = value
            else:
                data[key] = value

        print(data)

        if data['type'] == 'music_control':
            data['room_state'] = await self.music_control(event['action_data'])
        elif data['type'] == 'get_room_state':
            data['room_state'] = util.get_room_state(self.scope['user'], self.get_room().code)

        await self.send(text_data=json.dumps(data))

    # RECEIVE FUNCTION (WILL CALL FOR USER)
    async def receive(self, text_data):
        data = json.loads(text_data)

        if 'type' in data:
            out_data = {}

            type = data['type']

            out_data['type'] = 'room_send'
            out_data['message_type'] = type

            if type == 'music_control':
                out_data['action_data'] = data['data']

            await self.channel_layer.group_send(
                self.group_name, out_data
            )

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

    @database_sync_to_async
    def music_control(self, data):
        action = data['action']
        offset = data['offset'] if 'offset' in data else None

        user = self.scope['user']

        self.base_control(user.username, action, offset = offset)

        time.sleep(.1)

        return util.get_room_state(user, self.get_room().code)

    ##### SPOTIFY FUNCTIONS #####

    def base_control(self, username, option, offset = None):
        endpoint = spotify.player_endpoint + option

        user = User.objects.filter(username = username)

        if user.exists():
            user = user[0]

            data = {}

            if offset is not None:
                data['context_uri'] = 'spotify:playlist:' + str(self.get_room().playlist_id)

                data['offset'] = {
                    'position': offset
                }

            if option in self.put_methods:
                r = spotify.put(user, endpoint, data = data)
            elif option in self.post_methods:
                r = spotify.post(user, endpoint, data = data)

            if r.status_code not in range(200, 299):
                return False

            return True

        return False