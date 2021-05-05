from django.contrib.auth.models import User
from django.db import models
from django.utils import timezone

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

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete = models.CASCADE)
    access_token = models.CharField(max_length = 200)
    refresh_token = models.CharField(max_length = 200)
    authorized = models.BooleanField(default = False)
    most_recent_room = models.ForeignKey('Room', blank = True, null = True, on_delete = models.CASCADE, related_name = 'most_recent_name')

    icon_image = models.CharField(max_length = 100, choices = ProfilePicture.IMAGE_CHOICES, default = ProfilePicture.BABY_YODA)
    icon_color = models.CharField(max_length = 6, default = 'ffffff')
    background_color = models.CharField(max_length = 6, default = '07ace5')

    def __str__(self):
        return self.user.username

class Room(models.Model):
    code = models.CharField(max_length = 30)
    title = models.CharField(max_length=150, default="New Room")
    leader = models.ForeignKey(User, on_delete=models.CASCADE)
    time_created = models.DateTimeField(auto_now_add=True)
    playlist_id = models.CharField(max_length = 50, null = True)
    playlist_image_url = models.CharField(max_length = 250, null = True, blank = True)
    offset = models.IntegerField(default = 0, blank = True)
    playing = models.BooleanField(default = False, blank = True)
    progress = models.IntegerField(default = 0, blank = True)
    progress_time = models.DateTimeField(null = True, blank = True)
    users = models.ManyToManyField(User, blank = True, related_name = 'users')
    active_users = models.ManyToManyField(User, blank = True, related_name = 'active_users')

    def __str__(self):
        return self.code

    def is_active(self):
        return self.active_users.count() > 0
    
    def others_active(self, user):
        return (self.active_users.count() - 1 if user in self.active_users.all() else 0) > 0

class Playlist(models.Model):
    room = models.OneToOneField(Room, on_delete = models.CASCADE)
    song_index = models.IntegerField(default = 0, blank = True)
    progress_ms = models.IntegerField(default = 0, null = True, blank = True)
    last_action = models.DateTimeField(null = True, blank = True)
    playing = models.BooleanField(default = False, blank = True)