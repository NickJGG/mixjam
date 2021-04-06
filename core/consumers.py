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
    put_methods = ['play', 'pause', 'seek']
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
                'type': 'request_connection',
                'data': {
                    'connection_state': {
                        'connection_type': 'join',
                        'user': self.scope['user'].username
                    }
                }
            }
        )

    # DISCONNECT FUNCTION
    async def disconnect(self, close_code):
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

        await self.offline()

    # RECEIVE FUNCTION (WILL CALL FOR USER)
    async def receive(self, text_data):
        request_data = json.loads(text_data)

        self.print_request(request_data)

        if 'type' not in request_data or 'data' not in request_data:
            pass

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
        simple_actions = ['play', 'pause', 'next', 'previous']

        request_data = request_data['data']

        request_action = request_data['action']
        request_action_data = request_data['action_data']

        user = self.scope['user']

        method_data = {}
        method_params = {}

        if request_action != 'get_state':
            endpoint_option = request_action

            #region Actions

            if request_action in simple_actions:
                pass
            elif request_action == 'seek':
                method_params['position_ms'] = request_action_data['seek_ms']
            elif request_action == 'play_direct':
                endpoint_option = 'play'

                method_data['context_uri'] = 'spotify:playlist:' + str(self.get_room().playlist_id)
                method_data['offset'] = {
                    'position': request_action_data['offset']
                }

            #endregion

            endpoint = spotify.player_endpoint + endpoint_option

            if endpoint_option in self.put_methods:
                r = spotify.put(user, endpoint, data = method_data, params = method_params)
            elif endpoint_option in self.post_methods:
                r = spotify.post(user, endpoint, data = method_data)

            if r.status_code not in range(200, 299):
                return False

            time.sleep(.1)
    
        await self.response_send('playlist', util.get_room_state(user, self.get_room().code))

    async def request_chat(self, request_data):
        pass

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