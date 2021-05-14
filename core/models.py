import os

from django.shortcuts import reverse
from django.contrib.auth.models import User
from django.db import models
from django.utils import timezone
from django.utils.crypto import get_random_string

from channels.db import database_sync_to_async

from . import util

class ProfilePicture(models.Model):
    BABY_YODA = 'baby-yoda'
    BRUTUS = 'brutus'
    ELF = 'elf'
    BENDER = 'futurama-bender'
    SCREAM = 'scream'

    IMAGE_CHOICES = [
        (BABY_YODA, 'Baby Yoda'),
        (BRUTUS, 'Brutus'),
        (ELF, 'Elf'),
        (BENDER, 'Bender'),
        (SCREAM, 'Scream'),
    ]

class RoomMode(models.Model):
    PUBLIC = 'public'
    PRIVATE = 'private'
    CLOSED = 'closed'

    MODE_CHOICES = [
        (PUBLIC, 'Public'),
        (PRIVATE, 'Private'),
        (CLOSED, 'Closed'),
    ]

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete = models.CASCADE)
    tag_line = models.CharField(max_length = 50, default = 'Syncer')
    access_token = models.CharField(max_length = 200)
    refresh_token = models.CharField(max_length = 200)
    authorized = models.BooleanField(default = False)
    most_recent_room = models.ForeignKey('Room', blank = True, null = True, on_delete = models.SET_NULL, related_name = 'most_recent_name')

    icon_image = models.CharField(max_length = 100, choices = ProfilePicture.IMAGE_CHOICES, default = ProfilePicture.BABY_YODA)
    icon_color = models.CharField(max_length = 6, default = 'ffffff')
    background_color = models.CharField(max_length = 6, default = '07ace5')

    def __str__(self):
        return self.user.username

class Room(models.Model):
    code = models.CharField(max_length = 30)
    title = models.CharField(max_length=150, default="New Room")
    description = models.CharField(max_length = 1000, default = "")
    banner_color = models.CharField(max_length = 6, null = True, blank = True)
    mode = models.CharField(max_length = 50, choices = RoomMode.MODE_CHOICES, default = RoomMode.PRIVATE)

    invite_code = models.CharField(max_length = 6, null = True, blank = True)
    invite_time = models.DateTimeField(blank = True, null = True)

    leader = models.ForeignKey(User, on_delete=models.CASCADE)
    time_created = models.DateTimeField(auto_now_add=True)

    playlist_id = models.CharField(max_length = 50, null = True)
    playlist_image_url = models.CharField(max_length = 250, null = True, blank = True)

    users = models.ManyToManyField(User, blank = True, related_name = 'users')
    active_users = models.ManyToManyField(User, blank = True, related_name = 'active_users')

    def __str__(self):
        return self.code

    def is_active(self):
        return self.active_users.count() > 0
    
    def others_active(self, user):
        return (self.active_users.count() - 1 if user in self.active_users.all() else 0) > 0
    
    def get_site_url(self):
        return 'http://localhost:8000' if os.environ.get(
            'DJANGO_DEVELOPMENT') else 'http://syncified.herokuapp.com'

    def get_invite_link(self):
        self.check_invite()

        return self.get_site_url() + reverse('invite', kwargs = {
            'invite_code': self.invite_code
        })

    def new_invite(self):
        self.invite_code = get_random_string(length=6)
        self.invite_time = timezone.now()

        self.save()

    def check_invite(self):
        if self.mode == RoomMode.PUBLIC:
            return True
        elif self.invite_time is not None and (timezone.now() - self.invite_time).total_seconds() / 3600 < 24:
            return True
        else:
            self.new_invite()
        
        return False

class Playlist(models.Model):
    room = models.OneToOneField(Room, on_delete = models.CASCADE)
    song_index = models.IntegerField(default = 0, blank = True)
    progress_ms = models.IntegerField(default = 0, null = True, blank = True)
    last_action = models.DateTimeField(null = True, blank = True)
    last_song_end = models.DateTimeField(null = True, blank = True)
    playing = models.BooleanField(default = False, blank = True)

    def get_progress(self, user):
        if self.playing:
            progress_ms = util.get_adjusted_progress(self.room)
        else:
            progress_ms = self.progress_ms

        return progress_ms

    def song_end(self):
        now = timezone.now()

        if self.last_song_end is None or (now - self.last_song_end).total_seconds() > 5:
            self.last_song_end = now
            self.save()

            self.next_song()

            return True
        
        return False

    def previous_song(self):
        self.song_index = self.song_index - 1 if self.song_index > 0 else 0
        self.progress_ms = 0
        self.save()
    
    def next_song(self):
        self.song_index += 1
        self.progress_ms = 0
        self.save()

    @database_sync_to_async
    def restart(self):
        self.song_index = 0
        self.progress_ms = 0
        self.save()