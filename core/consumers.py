import json

from datetime import datetime

from django.template.loader import render_to_string

from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncWebsocketConsumer

from .models import *
from . import util, spotify

class UserConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        user = self.get_user()

        self.room_name = user.username
        self.group_name = 'user_%s' % self.room_name

        await self.channel_layer.group_add(
            self.group_name,
            self.channel_name
        )

        await self.accept()

        user.userprofile.go_online()

        if user.userprofile.online_count == 1:
            for friend in user.userprofile.friends.all():
                active_room = Room.objects.filter(users = friend, active_users = friend)

                if active_room.exists():
                    active_room = active_room[0]
                else:
                    active_room = None

                await self.channel_layer.group_send(
                    'user_%s' % friend.username,
                    {
                        'type': 'request_connection',
                        'data': {
                            'connection_state': {
                                'connection_type': 'online',
                                'user': {
                                    'username': user.username
                                },
                                'friend_block': render_to_string('core/blocks/side-panel-items/friend.html', {
                                    'friend': user,
                                    'user': friend,
                                    'room': active_room
                                })
                            }
                        }
                    }
                )

    # DISCONNECT FUNCTION
    async def disconnect(self, close_code):
        user = self.get_user()

        user.userprofile.go_offline()

        if user.userprofile.online_count == 0:
            for friend in user.userprofile.friends.all():
                active_room = Room.objects.filter(users = friend, active_users = friend)

                if active_room.exists():
                    active_room = active_room[0]
                else:
                    active_room = None

                await self.channel_layer.group_send(
                    'user_%s' % friend.username,
                    {
                        'type': 'request_connection',
                        'data': {
                            'connection_state': {
                                'connection_type': 'offline',
                                'user': {
                                    'username': user.username
                                },
                                'friend_block': render_to_string('core/blocks/side-panel-items/friend.html', {
                                    'friend': user,
                                    'user': friend,
                                    'room': active_room
                                })
                            }
                        }
                    }
                )

        await self.channel_layer.group_discard(
            self.group_name,
            self.channel_name
        )

    async def receive(self, text_data):
        request_data = json.loads(text_data)

        #request_type = request_data['type']
        #request_action = request_data['data']['action']

        user = self.get_user()

        await self.channel_layer.group_send(
            self.group_name, request_data
        )

    async def response_send(self, type, response_data):
        await self.send(text_data=json.dumps({
            'type': type,
            'response_data': response_data
        }))

    async def request_connection(self, request_data):
        await self.response_send('connection', request_data)

    async def request_notification(self, request_data):
        await self.response_send('notification', request_data)
    
    def get_user(self):
        return User.objects.get(username = self.scope['user'])

class RoomConsumer(AsyncWebsocketConsumer):
    put_methods = ['play', 'pause', 'seek']
    post_methods = ['previous', 'next']

    playlist_to_history = {
        'play': 'resumed',
        'play_direct': 'played',
        'pause': 'paused',
        'previous': 'skipped back to',
        'next': 'skipped to',
        'seek': 'seeked to',
    }

    # CONNECT FUNCTION
    async def connect(self):
        room_code = self.scope['url_route']['kwargs']['room_code']
        user = self.get_user()
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

        response = await spotify.update_play(user, room)

        devices, active, volume = await self.get_devices()

        await self.send(text_data=json.dumps({
            'type': 'devices',
            'response_data': {
                'devices': devices,
                'active': active,
                'volume': volume
            }
        }))

        await self.request_playlist({
            'data': {
                'action': 'get_state'
            }
        })

        await self.send_history_entry('join', user, 'joined', before_subject = render_to_string('core/blocks/profile-picture.html', {
            'width': '100%',
            'height': '100%',
            'user': user
        }))

    # DISCONNECT FUNCTION
    async def disconnect(self, close_code):
        await self.offline()

        user = self.get_user()
        room = self.get_room()

        await self.send_history_entry('leave', user, 'left', before_subject = render_to_string('core/blocks/profile-picture.html', {
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

        user = self.get_user()
        room = self.get_room()

        self.print_request(request_data)

        if request_type == 'playlist':
            return_data = spotify.update_playlist(user, room, request_data['data'])

            if request_action == 'song_end' and not return_data:
                return

            request_data['data']['action_data']['user'] = user.username
        elif request_data['type'] == 'chat':
            request_data['data']['action_data']['user'] = {
                'username': user.username,
                'color': user.userprofile.color
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
            elif request_action == 'select_device':
                device_id = request_data['data']['action_data']['device_id']

                response = spotify.select_device(user, device_id)

                try:
                    if response.status_code == 204:
                        await spotify.update_play(user, room)
                except:
                    pass

                try:
                    devices, active, volume = await self.get_devices()

                    await self.send(text_data=json.dumps({
                        'type': 'devices',
                        'response_data': {
                            'devices': devices,
                            'active': active,
                            'volume': volume
                        }
                    }))
                except:
                    pass

                return
            elif request_action == 'get_devices':
                try:
                    devices, active, volume = await self.get_devices()

                    await self.send(text_data=json.dumps({
                        'type': 'devices',
                        'response_data': {
                            'devices': devices,
                            'active': active,
                            'volume': volume
                        }
                    }))
                except:
                    pass

                return
            elif request_action == 'set_volume':
                volume_percent = request_data['data']['action_data']['volume_percent']

                response = await spotify.set_volume(user, volume_percent)

                return

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

        user = self.get_user()
        room = self.get_room()

        before_subject = None
        before_object = None

        await spotify.action(user, room, request_action, request_action_data)

        if request_action in self.playlist_to_history.keys():
            before_subject = render_to_string('core/blocks/profile-picture.html', {
                'width': '20px',
                'height': '20px',
                'user': User.objects.get(username = request_action_data['user'])
            })
    
        room_state = await spotify.get_room_state(user, room.code)
        room_state['song_block'] = render_to_string('core/blocks/room/playlist-song.html')

        await self.response_send('playlist', room_state)

        if before_subject is not None:
            await self.send_self_history_entry(request_action, request_action_data['user'], self.playlist_to_history[request_action], before_subject = before_subject, before_object = before_object)

    async def request_chat(self, request_data):
        request_data['data']['action_data']['user']['self'] = request_data['data']['action_data']['user']['username'] == self.get_user()

        await self.response_send('chat', request_data['data'])

    async def request_admin(self, request_data):
        request_data = request_data['data']

        request_action = request_data['action']
        request_action_data = request_data['action_data'] if 'action_data' in request_data else None

        user = self.get_user()
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

                    await self.send_history_entry(request_action, room.leader, 'kicked', request_action_data['user'], before_subject = render_to_string('core/blocks/profile-picture.html', {
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

    async def request_history(self, request_data):
        await self.response_send('history_entry', request_data)

    async def request_user_action(self, request_data):
        request_data = request_data['data']

        await self.response_send('user_action', request_data)

    async def request_connection(self, request_data):
        user = self.get_user()

        if request_data['data']['connection_state']['connection_type'] != 'kick':
            room = self.get_room()

            connection_user = User.objects.get(username = request_data['data']['connection_state']['user']['username'])

            request_data['data']['connection_state']['user']['user_block'] = render_to_string('core/blocks/side-panel-items/room-user.html', {
                'room_user': connection_user,
                'room': room,
                'user': user
            })
        else:
            self_kicked = request_data['data']['connection_state']['user']['username'] == user.username

            print(user, 'KICKED:', request_data['data']['connection_state']['user']['username'], self_kicked)

            request_data['data']['connection_state']['self_kicked'] = self_kicked

        await self.response_send('connection', request_data)

    async def send_history_entry(self, request_action, subject, action, object = None, before_subject = None, before_object = None):
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
                'type': 'request_history',
                'data': {
                    'request_action': request_action,
                    'block': render_to_string('core/blocks/room/history-entry.html', block_data)
                }
            }
        )

    async def send_self_history_entry(self, request_action, subject, action, object = None, before_subject = None, before_object = None):
        block_data = {
            'subject': subject,
            'action': action,
            'object': object,
            'before_subject': before_subject,
            'before_object': before_object
        }

        await self.response_send('request_history', {
            'data': {
                'request_action': request_action,
                'block': render_to_string('core/blocks/room/history-entry.html', block_data)
            }
        })

    # HELPER FUNCTIONS

    @database_sync_to_async
    def online(self):
        room = self.get_room()

        if room:
            room.active_users.add(self.get_user())

    @database_sync_to_async
    def offline(self):
        room = self.get_room()

        if room:
            room.active_users.remove(self.get_user())
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
        print('User: ' + self.get_user().username)
        print('\nType: ' + request_data['type'])
        print('Data: ' + json.dumps(request_data['data'], indent = 4))
        print('==================== END REQUEST ===\n')
    
    async def get_devices(self):
        active = False
        volume = 0

        user = self.get_user()

        raw_devices = await spotify.get_devices(user)

        # print('\n\n\n\n\n')
        # print(raw_devices)
        # print(raw_devices.status_code)
        # print(raw_devices.content)
        # print(raw_devices.json())

        devices = []

        try:
            for device in raw_devices.json()['devices']:
                if device['is_active']:
                    devices = [(render_to_string('core/blocks/room/device.html', {
                        'device': device
                    }))] + devices
                    
                    active = True

                    volume = device['volume_percent']
                else:
                    devices.append(render_to_string('core/blocks/room/device.html', {
                        'device': device
                    }))
            
            return devices, active, volume
        except:
            return None, None, None
    
    def get_user(self):
        return User.objects.get(username = self.scope['user'])